import os,sys
from flask import Flask, jsonify, flash, request, redirect, url_for
from werkzeug.utils import secure_filename
from loaderWrapper import LoaderWrapper
from langchain.text_splitter import TokenTextSplitter
from langchain.document_loaders import TextLoader
from db import DB
from queryLLM import QueryLLM

UPLOAD_FOLDER = '/tmp'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'epub'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/sources', methods=['GET'])
def get_sources():
    from db import DB
    db = DB()
    db.cursor.execute("select distinct cmetadata->>'source' AS source from public.langchain_pg_embedding;")
    rows = db.cursor.fetchall()
    return jsonify(rows)

# delete a source
@app.route('/sources/<string:source>', methods=['DELETE'])
def delete_source(source):
    from db import DB
    db = DB()
    db.cursor.execute("delete from public.langchain_pg_embedding where cmetadata->>'source' = '"+source+"';")
    return jsonify({'message': 'Source deleted'})

# upload a file
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(path)
            # load file
            loader = LoaderWrapper(path=path, type="file")
            documents = loader.load()
            print(documents,file=sys.stderr)
            text_splitter = TokenTextSplitter(chunk_size=500, chunk_overlap=100)
            texts = text_splitter.split_documents(documents)
            from db import DB
            db = DB()
            print(texts,file=sys.stderr)
            ids = db.vectorstore.add_documents(texts)
            print(ids,file=sys.stderr)
            return redirect("/",200)
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    '''


# Ask a question to your data
@app.route('/ask', methods=['POST'])
def ask():
	question = request.json.get('question')
	history_array = request.json.get('history', '')
	try:
		history = []
		for [answer, question] in history_array:
			history.append((answer, question))
	except:
		history = ""
	oracle = QueryLLM()
    #print(oracle.ask(question, history))
    #return jsonify({'message': 'Question answered'})
	return jsonify(oracle.ask(question, history))

if __name__ == '__main__':
    app.run(debug=True)