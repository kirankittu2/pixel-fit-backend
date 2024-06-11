from flask import Flask, render_template, request, redirect, make_response, jsonify
import os
import cv2
import json
import re
import bleach
from flask_cors import CORS
from werkzeug.utils import secure_filename
from database import connect_to_mysql
from mysql.connector import Error
from PIL import Image
import random
from datetime import datetime

UPLOAD_FOLDER = 'uploads'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = "uploads"
CORS(app, resources={r"/api/*": {"origins":[ "https://thepixelfit.com","https://www.thepixelfit.com" ]}})



@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file:
        file_path = os.path.join("uploads", file.filename)
        file.save(file_path)

        image_matrix = image_to_matrix(file_path)
        
        return json.dumps({'matrix': image_matrix.tolist()})
    return []

def image_to_matrix(image_path):
    image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)

    if image is None:
        raise ValueError("Image not found or unable to open")
    
    if len(image.shape) == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
    return image

def validate_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def sanitize_input(input_string):
    return bleach.clean(input_string)

@app.route('/store', methods=['POST'])
def handle_form_data():
    conn, cursor = connect_to_mysql()
    email = request.form.get('email')
    title = request.form.get('title')
    instagram = request.form.get('instagram')
    message = request.form.get('message')
    file = request.files.get('image')
    filetype = request.form.get('filetype')


    if(len(email) > 0):
        if not email or not validate_email(email.strip()):
            return {"success" : False, message: "Not a valid email"}
    
    if not title or not isinstance(title.strip(), str):
        return {"success" : False,  message: "Not a valid tile"}
    title = sanitize_input(title)

    if not instagram or not isinstance(instagram.strip(), str):
        return {"success" : False,  message: "Not a valid Instagram ID"}
    instagram = sanitize_input(instagram)

    if not message or not isinstance(message.strip(), str):
        return {"success" : False,  message: "Not a valid Message"}
    message = sanitize_input(message)

    if not file:
        return {"success" : False,  message: "Not a valid File"}
    
    if file.filename == '':
        return {"success" : False,  message: "Not a valid File"}
    
    if file:
        try:
            print(file)
            text_after_slash = filetype.split("/")[1];
            now = datetime.now()
            datetime_str = now.strftime("%Y%m%d%H%M%S")
            datetime_int = int(datetime_str)
            random_num = random.randint(1, 1000)
            result = datetime_int + random_num

            combined_string = instagram + "_" + str(result) 
            print(combined_string)
            secureFilename = secure_filename(combined_string + "."+ text_after_slash)
            print(secureFilename)
            file_path = os.path.join(UPLOAD_FOLDER, secureFilename)
            file.save(file_path)
        except Exception as e:
            return {"success" : False,  "message": str(e)}
        
    try:
        cursor.execute('INSERT INTO image_data (instagram_id, email, title, message, image_link, type) VALUES (%s, %s, %s, %s, %s, %s)', (instagram, email, title, message.upper(), combined_string, text_after_slash))
        conn.commit()

        cursor.close()
        conn.close()

        return {"success" : True, "message": "Successfully stored in Database"}
    
    except Error as e:
        print(f"Error: {e}")
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        return {"success": False, "message": str(e)}
      

@app.route('/details', methods=['POST'])
def get_details():
    conn, cursor = connect_to_mysql()
    id = request.form.get('image_link')
    print(id)
    if not id or not isinstance(id, str):
        return {"success" : False}
    id = sanitize_input(id)
    try:   
        cursor.execute('SELECT * FROM image_data WHERE image_link = %s', (id,))
        result = cursor.fetchall()
        
        if len(result) == 0:
            return {"success" : False}

        file_path = os.path.join("uploads", result[0]['image_link'] + "." + result[0]['type'])
        with Image.open(file_path) as img:
            img = img.resize((300, 533), Image.LANCZOS)
            img.save(file_path)
        image_matrix = image_to_matrix(file_path)

        cursor.close()
        conn.close()
        
        return json.dumps({'matrix': image_matrix.tolist(), "heading": result[0]['title'], "message": result[0]['message']})
            
    except Error as e:
        print(f"Error: {e}")
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        return {"success": False, "error": str(e)}


@app.route('/verify-id', methods=['POST'])
def verify_id():
    passw = request.form.get('passw')

    if not passw or not isinstance(passw, str):
        return {"success" : False,  "message": "Not a valid ID"}
    passw = sanitize_input(passw)
   
    if(passw):
        print(passw)
        check = passw == "v84bO0KuM2tr"
        if(check):
            return {"success" : True,  "message": "Not a valid ID"}
        else:
            return {"success" : False,  "message": "Not a valid ID"}
    
    return {"success" : False,  "message": "Not a valid ID"}

def set_cookie():
    response = make_response("Setting a cookie!")
    response.set_cookie("pixel-access", "approved", max_age=3600)
    return response

@app.route('/pending', methods=['GET'])
def pending():
    conn, cursor = connect_to_mysql()
    id = 0
    
    try:  
        cursor.execute('SELECT id, instagram_id, image_link, created_on FROM image_data WHERE img_generated = %s', (id,))
        result = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify(result)

    except Error as e:
        print(f"Error: {e}")
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        return jsonify({"success": False, "error": str(e)})
    
@app.route('/accepted', methods=['GET'])
def approved():
    conn, cursor = connect_to_mysql()
    id = 1
 
    try:  
        cursor.execute('SELECT id, instagram_id, image_link, created_on FROM image_data WHERE img_generated = %s AND payment_success = %s', (id, 0))
        result = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify(result)

    except Error as e:
        print(f"Error: {e}")
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        return jsonify({"success": False, "error": str(e)})
    

@app.route('/approved', methods=['GET'])
def accepted():
    conn, cursor = connect_to_mysql()
    id = 1
    
    try:
        id = 0
        cursor.execute('SELECT COUNT(*) as count FROM image_data WHERE img_generated = %s', (id,))
        pending = cursor.fetchall()

        id = 1
        cursor.execute('SELECT COUNT(*) as count FROM image_data WHERE img_generated = %s AND payment_success = %s', (id, 0))
        approved = cursor.fetchall()

        id = 1
        cursor.execute('SELECT COUNT(*) as count FROM image_data WHERE payment_success = %s', (id,))
        accepted = cursor.fetchall()

        cursor.execute('SELECT COUNT(*) as count FROM image_data')
        total = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify([pending, approved, accepted, total])

    except Error as e:
        print(f"Error: {e}")
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        return jsonify({"success": False, "error": str(e)})
    

@app.route('/approve', methods=['POST'])
def approve():
    conn, cursor = connect_to_mysql()
    id = request.form.get('id')

    if not id or not isinstance(id, str):
        return {"success" : False,  "message": "Not a valid ID"}
    id = sanitize_input(id)
    print(id)
    try:
        update_query = """
            UPDATE image_data
            SET img_generated = %s
            WHERE id = %s
            """
        values = (1, id)
        cursor.execute(update_query, values)
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"success": True})

    except Error as e:
        print(f"Error: {e}")
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        return jsonify({"success": False, "error": str(e)})
    

@app.route('/accept', methods=['POST'])
def accept():
    conn, cursor = connect_to_mysql()
    id = request.form.get('id')

    if not id or not isinstance(id, str):
        return {"success" : False,  "message": "Not a valid ID"}
    id = sanitize_input(id)
    print(id)
    try:
        update_query = """
            UPDATE image_data
            SET payment_success = %s
            WHERE id = %s
            """
        values = (1, id)
        cursor.execute(update_query, values)
        conn.commit()
        
        cursor.close()
        conn.close()

        return jsonify({"success": True})

    except Error as e:
        print(f"Error: {e}")
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        return jsonify({"success": False, "error": str(e)})



if __name__ == '__main__':
    app.run(debug=True)