from flask import Flask, render_template, jsonify, request
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from shutil import copyfile
from PIL import Image
import cv2
from skimage import exposure
import numpy as np

import os
import qrcode
import re
import shutil

app = Flask(__name__)

# Lấy thông tin kết nối từ biến môi trường (Render cung cấp DATABASE_URL)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://user:CRLMC7hvK0rCEfvn6Nr2YJUtJetOR0ug@dpg-d43if0uuk2gs73954uq0-a.singapore-postgres.render.com/coasterdpi16_db_x5vo')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
id_CoasterDB = '654321'
id_HtDB = '999999'
now = datetime.now()
formatted_date = now.strftime("%Y.%m.%d")

def test_db_connection():
    try:
        # Thử kết nối tới cơ sở dữ liệu
        db.session.execute(text('SELECT 1'))  # Truy vấn đơn giản để kiểm tra kết nối
        print("Kết nối đến cơ sở dữ liệu PostgreSQL thành công!")
    except Exception as e:
        print(f"Lỗi kết nối cơ sở dữ liệu: {e}")

class NumPhotosPrinted(db.Model):
    __tablename__ = 'numphotosprinted'  # Tên bảng
    id = db.Column(db.String(50), primary_key=True)  # Khóa chính
    quantity = db.Column(db.Integer)

class NumPhotosPrintedHt(db.Model):
    __tablename__ = 'numphotosprintedht'  # Tên bảng
    id = db.Column(db.String(50), primary_key=True)  # Khóa chính
    standard = db.Column(db.Integer)
    full = db.Column(db.Integer)
    extra = db.Column(db.Integer)
    customer = db.Column(db.Integer)
    quantity = db.Column(db.Integer)
    quantity_backup = db.Column(db.Integer)

@app.route('/')
def index():
    try:
        test_db_connection()
        # delete = db.session.execute(text("DELETE FROM numphotosprintedht WHERE id = :id"), {'id': '123456'})
        # db.session.commit()
        result = db.session.execute(text("SELECT to_regclass('public.numphotosprintedht')"))
        table_exists = result.scalar()  # Dùng scalar() để lấy kết quả từ câu lệnh SQL
        
        
        if not table_exists:
            db.create_all()
            print('Database created successfull')
        else:
            print('nnn')
        return render_template('index.html')
    except Exception as e:
        return f"Lỗi khi kiểm tra hoặc tạo bảng: {str(e)}" 

@app.route('/get_photos_printed', methods=['GET'])
def get_photos_printed():
    # db.session.execute(text("INSERT INTO numphotosprinted VALUES (:id, :quantity)"), {"id": id_CoasterDB, "quantity": 0})
    # db.session.commit()
    folder_path_pos1 = r'\\Coasterpos1\prints\Archive'
    folder_path_pos2 = r'\\Coasterpos2\prints\Archive'
    folder_path_pos3 = r'\\Coasterpos3\prints\Archive'

    path_pos1 = folder_path_pos1 + f'\\{formatted_date}\\s6x8'
    path_pos2 = folder_path_pos2 + f'\\{formatted_date}\\s6x8'
    path_pos3 = folder_path_pos3 + f'\\{formatted_date}\\s6x8'

    photos_printed_pos1 = get_count_files(path_pos1)
    photos_printed_pos2 = get_count_files(path_pos2)
    photos_printed_pos3 = get_count_files(path_pos3)
    
    today = datetime.now().strftime("%d.%m.%Y")
    print(today)
    file_count = 0
    if ((photos_printed_pos1 == 0 and photos_printed_pos2 == 0 and photos_printed_pos3 == 0) and not os.path.exists(folder_path_pos2)):
        result = db.session.execute(text("SELECT quantity FROM numphotosprinted WHERE id = :id"), {"id": id_CoasterDB})
        value = result.fetchone()
        file_count = value[0]
    else:
        file_count = photos_printed_pos1 + photos_printed_pos2 + photos_printed_pos3
        try:
            db.session.execute(text("UPDATE numphotosprinted SET quantity = :quantity WHERE id = :id"), {"quantity": file_count, "id": id_CoasterDB})
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Lỗi: {e}")

    return jsonify({'today': today, 'file_count': file_count}) 

def get_count_files(folder_path):
    try:
        return len([name for name in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, name))])
    except Exception as e:
        return 0

def get_count_folder(folder_path):
    try:
        return len([name for name in os.listdir(folder_path)])
    except Exception as e:
        return 0
    
@app.route('/show_qrcode', methods=['POST'])
def show_qrcode():
    urlExample = 'https://sharepix.com.au/ht/uploads/'
    numQr = request.json.get('numQr')

    folder_path_pos1 = r'\\Coasterpos1\prints\Archive'
    folder_path_pos2 = r'\\Coasterpos2\prints\Archive'
    folder_path_pos3 = r'\\Coasterpos3\prints\Archive'

    path_pos1 = folder_path_pos1 + f'\\{formatted_date}\\s6x8'
    path_pos2 = folder_path_pos2 + f'\\{formatted_date}\\s6x8'
    path_pos3 = folder_path_pos3 + f'\\{formatted_date}\\s6x8'

    file_pattern = re.compile(r'\d{3}-\w{3}-' + re.escape(str(numQr)) + r'\.jpg')

    def search_in_folder(folder_path):
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                print(file)
                if file_pattern.match(file):  # Kiểm tra nếu tên file khớp với pattern
                    return file  # Trả về tên file, không phải đường dẫn

        return None  # Nếu không tìm thấy tệp nào khớp

    url = ''
    for path in [path_pos1, path_pos2, path_pos3]:
        print(path)
        result = search_in_folder(path)
        print(result)
        if result:
            url = urlExample + result
            break

    if url == '':
        return jsonify({'result': False})

    qr = qrcode.QRCode(
        version=1,  
        error_correction=qrcode.constants.ERROR_CORRECT_L, 
        box_size=10, 
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill='black', back_color='white')
    img_name = numQr + '.png'

    # Lưu hình ảnh vào thư mục /images
    image_path = os.path.join('static/qrcode_backup/', img_name)  # Đặt đường dẫn lưu tệp

    # Lưu hình ảnh vào tệp
    img.save(image_path, 'PNG')

    return jsonify({'result': True, 'path': image_path})
    
@app.route('/get_photos_printed_ht', methods=['GET'])
def get_photos_printed_ht():
    date_now = now.strftime("%Y_%m_%d")
    target_time = now.replace(hour=16, minute=0, second=0, microsecond=0)
    path_ops = r"\\PRINTSERVER1\CapImages\Ops"
    customer_path = r"\\PRINTSERVER1\Customers"
    photo_standard = 0
    photo_extra = 0
    photo_full = 0
    photo_customer = get_count_folder(customer_path)
    try:
        for file_name in os.listdir(path_ops):
            if file_name.startswith(date_now) and file_name.endswith('_Log.txt'):
                duong_dan_file = os.path.join(path_ops, file_name)

                with open(duong_dan_file, 'r') as file:
                    lines = file.readlines()

                    # Lặp qua từng dòng để tính tổng tiền
                    for line in lines:
                        # Tách thông tin từ dòng
                        thong_tin = line.strip().split(', ')

                        # Lấy giá trị từ cột thứ 6 (số tiền)
                        so_tien = int(thong_tin[5])

                        # Lấy loại gói từ cột thứ 1
                        loai_goi = thong_tin[1]

                        # Tính tổng tiền dựa trên loại gói
                        if "Standard" in loai_goi:
                            photo_standard += 1
                        elif "Extra" in loai_goi:
                            photo_extra += 1
                        elif "Full" in loai_goi:
                            photo_full += 1
    except Exception as e:
        db.session.rollback()
        print(f"Lỗi: {e}")
        
    folder_path_pos1 = f"\\PRINTSERVER1\\prints\\Archive"
    folder_path_pos2 = f"\\PRINTSERVER3\\prints\\Archive"

    path_pos1 = folder_path_pos1 + f'\\{formatted_date}\\s8x10'
    path_pos2 = folder_path_pos2 + f'\\{formatted_date}\\s8x10'

    photos_printed_pos1 = get_count_files(path_pos1)
    photos_printed_pos2 = get_count_files(path_pos2)


    file_stand = 0
    file_full = 0
    file_extra = 0
    file_customer = 0
    file_count = 0
    # db.session.execute(text("INSERT INTO numphotosprintedht VALUES (:id, :standard, :full, :extra, :customer, :quantity, :quantity_backup)"), {"id": id_HtDB ,"standard": 0, "full": 0, "extra": 0, "customer": 0, "quantity": 0, "quantity_backup": 0})
    # db.session.commit()

    result = db.session.execute(text("SELECT * FROM numphotosprintedht WHERE id = :id"), {"id": id_HtDB})
    value = result.fetchone()

    print(value)

    if (photos_printed_pos1 == 0 and photos_printed_pos2 == 0 and not os.path.exists(folder_path_pos1)):
        file_stand = value[1]
        file_full = value[2]
        file_extra = value[3]
        file_customer = value[4]
        file_count = value[5]
    else:
        if now > target_time and os.path.exists(folder_path_pos1) and not os.path.exists(folder_path_pos2):
            file_count = photos_printed_pos1 + value[5]
        else:
            file_count = photos_printed_pos1 + photos_printed_pos2
        file_stand = photo_standard
        file_full = photo_full
        file_extra = photo_extra
        file_customer = photo_customer
        try:
            db.session.execute(text("""UPDATE numphotosprintedht SET standard = :standard, "full" = :photo_full, extra = :extra, customer = :customer, quantity = :quantity, quantity_backup = :quantity_backup WHERE id = :id"""),
                            {"standard": photo_standard, "photo_full": photo_full, "extra": photo_extra, "customer": file_customer, "quantity": file_count, "quantity_backup": photos_printed_pos2, "id": id_HtDB})
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Lỗi: {e}")

    return jsonify({'file_stand': file_stand, 'file_full': file_full, 'file_extra': file_extra, 'file_customer': file_customer, 'file_count': file_count}) 

png_img_path = ''
img_name_temporary = ''
png_temp_path_add_check = ''
# Route API để kiểm tra sự tồn tại của hình ảnh
@app.route('/check_image', methods=['POST'])
def check_image():
    global png_img_path, img_name_temporary, png_temp_path_add_check

    img_number_received = request.json.get('img_number')  # Nhận số từ frontend

    # save name image to use later
    img_name_temporary = img_number_received

    # đường dẫn thực tế tới hình ảnh
    file_path = os.path.join(r'\\PRINTSERVER1\CapImages', f'img{img_number_received}.png')

    # check if it exists
    print(file_path)
    checked = os.path.isfile(file_path)
    if checked:

        # if exists, copy to project directory
        png_temp_path_add_check = f'static/temp/add_imgs/{img_number_received}.png'
        copyfile(file_path, png_temp_path_add_check)

        # use later var
        png_img_path = file_path
        return jsonify({'path': png_temp_path_add_check})
    else:
        return 'error'

destination_path = ''
existed_dir_path = ''
destination_path_added = ''
@app.route('/find_directory', methods=['POST'])
def find_directory():
    global destination_path_added, destination_path, existed_dir_path

    base_folder = r'\\PRINTSERVER1\Customers'
    last_five_digits = request.form['last_five_digits']

    # Lấy danh sách tất cả các thư mục trong thư mục gốc
    all_folders = [f for f in os.listdir(base_folder) if os.path.isdir(os.path.join(base_folder, f))]

    # Tìm kiếm thư mục tương ứng với 5 hoặc 6 số cuối
    if len(last_five_digits) <= 5:
        matching_folder = next((folder for folder in all_folders if folder[-5:] == last_five_digits), None)
        existed_dir_path = matching_folder
    else:
        matching_folder = next((folder for folder in all_folders if folder[-6:] == last_five_digits), None)
        existed_dir_path = matching_folder

    if matching_folder:
        # destination path to add after created
        destination_path_added = base_folder + '\\' + matching_folder

        img_path = base_folder + "/" + matching_folder + '/uploaded_14.jpg'
        img_path2 = base_folder + "/" + matching_folder + '/uploaded_24.jpg'
        destination_path = f'static/temp/add_imgs/{last_five_digits}.jpg'

        print(last_five_digits, img_path, destination_path)
        try:
            checked = os.path.isfile(img_path)
            if checked:
                copyfile(img_path, destination_path)
            else:
                copyfile(img_path2, destination_path)
            # Thực hiện sao chép tệp tin
            # copyfile(img_path, destination_path)

            # Trả về đường dẫn mới thông qua JSON
            return jsonify({"file_path": destination_path, "msg": "Hình ảnh được tìm thấy"})
        except Exception as e:
            print(e)
            return jsonify({"msg": 'Cant handle image file'})
    else:
        print('cant find this photos')
        return jsonify({"msg": "Hình ảnh không được tìm thấy !"})

@app.route('/process', methods=['POST'])
def process():
    # check if it already added before adding
    flag = True
    # print('existed dir to adding', existed_dir_path)   # existed dir to adding 010HGQ41559
    # print('img number to adding', img_name_temporary)  # img number to adding 10058

    customer_path = r''

    existed_file_check = f'\\PRINTSERVER1\\Customers\\{existed_dir_path}\\{img_name_temporary}_bg3.png'
    existed_file_check_uploaded = f'\\PRINTSERVER1\\Customers\\{existed_dir_path}\\uploaded_{img_name_temporary}_bg3.png'  # uploaded_32564_bg3.png

    flag_file_check = os.path.isfile(existed_file_check)
    flag_file_uploaded_check = os.path.isfile(existed_file_check_uploaded)
    if flag_file_check:
        flag = False
    elif flag_file_uploaded_check:
        flag = False
    else:
        flag = True

    # check function before adding, flag = True, run function, else return ADDED
    if flag:
        if png_img_path != '':

            # Mở tệp ảnh đối tượng
            obj = Image.open(png_img_path).convert("RGBA")
            # Mở tệp ảnh nền cabin (ảnh nhỏ)
            # w 2008 / h 2008
            resized_dimensions = (int(3008 * 0.6), int(2008 * 0.6))

            obj_cc = obj.resize(resized_dimensions)  # in case

            objcc_alpha = obj_cc.split()[3]
            back_cabin = Image.open("static/background/back_cabin.png").convert("RGBA")
            front_cabin = Image.open("static/background/front_cabin.png").convert("RGBA")
            front_cabin_alpha = front_cabin.split()[3]

            # Chỉnh vị trí của đối tượng trên ảnh cabin
            x_position = 1020  # horizontal_ left
            y_position = 180  # vertical_ upper
            back_cabin.paste(obj_cc, (x_position, y_position), objcc_alpha)
            back_cabin.paste(front_cabin, (0, 0), front_cabin_alpha)
            # back_cabin.show()

            # Mở tệp ảnh các nền khác
            obj_other_alpha = obj.split()[3]

            bg1 = Image.open("static/background/BKG2.jpg").convert("RGBA")
            bg2 = Image.open("static/background/BKG3.jpg").convert("RGBA")
            bg3 = Image.open("static/background/BKG4.jpg").convert("RGBA")

            # Chỉnh vị trí của đối tượng trên các nền khác
            x_position_other_bg = 400  # horizontal position
            y_position_other_bg = 250  # vertical position

            bg1.paste(obj, (x_position_other_bg, y_position_other_bg), obj_other_alpha)
            bg2.paste(obj, (x_position_other_bg, y_position_other_bg), obj_other_alpha)
            bg3.paste(obj, (x_position_other_bg, y_position_other_bg), obj_other_alpha)

            # Lưu các hình ảnh đã tạo ra

            back_cabin.save(f'{destination_path_added}\\{img_name_temporary}_back_cabin.png')
            bg1.save(f'{destination_path_added}\\{img_name_temporary}_bg1.png')
            bg2.save(f'{destination_path_added}\\{img_name_temporary}_bg2.png')
            bg3.save(f'{destination_path_added}\\{img_name_temporary}_bg3.png')

            # print('added new picture')
            return jsonify({'result': True})
        else:
            return 'Đã có lỗi xảy ra!!!'
    else:
        return jsonify({'result': False})

raw_temp_path = ''
raw_number = ''
@app.route('/check_image_error', methods=['POST'])
def check_image_error():
    global raw_temp_path, raw_number
    img_number = request.json.get('img_number')  # Nhận số từ frontend

    # use later when remove
    raw_number = img_number

    # đường dẫn thực tế tới hình ảnh
    file_path = os.path.join(r'\\PRINTSERVER1\CapImages', f'img{img_number}.png')

    # check if it exists
    checked = os.path.isfile(file_path)
    if checked:

        # copy hình tách nền lỗi
        des_temp_err_img = f'static/temp/error/{img_number}.png'

        print(des_temp_err_img)
        copyfile(file_path, des_temp_err_img)

        # nếu hình tách nền xanh có tồn tại, tìm hình chưa tách nền
        raw_img_path = os.path.join(r'\\PRINTSERVER1\CapImages\RawFiles', f'img{img_number}.jpg')
        raw_temp_path = raw_img_path

        # if exists, copy to project directory
        des_temp_path_raw = f'static/temp/raw/{img_number}.jpg'
        copyfile(raw_img_path, des_temp_path_raw)

        return jsonify({'result': True, 'path': des_temp_err_img, 'raw_path': des_temp_path_raw})
    else:
        print(checked)
        return jsonify({'result': False})


@app.route('/reload_img', methods=['POST'])
def reload_img():
    img_error = f'static/temp/error/{raw_number}.png'
    output_path = f'//PRINTSERVER1/CapImages/img{raw_number}.png'
    img = Image.open(img_error)
    img.save(output_path)
    return jsonify({'img_path': img_error})

@app.route('/remove_bg', methods=['POST'])
def remove_bg():
    global raw_number

    firstNum = request.json.get('firstNum')
    lastNum = request.json.get('lastNum')

    # Load image
    img = cv2.imread(raw_temp_path)

    # Convert to LAB color space
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)

    # Extract A channel
    A = lab[:, :, 1]

    # màu khác xanh: 106
    # màu xanh đậm: 103
    # màu xanh dương nhạt: 101
    test = cv2.inRange(A, firstNum, lastNum)

    # Threshold A channel
    _, thresh = cv2.threshold(test, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Blur thresholded image
    blur = cv2.GaussianBlur(thresh, (15, 15), sigmaX=4, sigmaY=0, borderType=cv2.BORDER_DEFAULT)

    # Stretch intensity
    mask = exposure.rescale_intensity(blur, in_range=(127.5, 255), out_range=(0, 255)).astype(np.uint8)

    # Add mask to image as alpha channel
    result = img.copy()
    # Chuyển đổi ảnh sang không gian màu HLS
    hls = cv2.cvtColor(result, cv2.COLOR_BGR2HLS)

    # Tách các kênh H, L, S
    h, l, s = cv2.split(hls)

    # Giảm độ bão hòa (S channel)
    s = cv2.multiply(s, 0.9)  # Giảm độ bão hòa xuống 50%, có thể thử với giá trị khác tùy ý

    # Gộp lại các kênh và chuyển về không gian BGR
    result_hls = cv2.merge((h, l, s))
    result = cv2.cvtColor(result_hls, cv2.COLOR_HLS2BGR)
    b, g, r = cv2.split(result)
    result = cv2.merge((b, g, r, mask))

    # Save output images
    output_path = f'//PRINTSERVER1/CapImages/img{raw_number}.png'
    backup_result_path = f'static/temp/result/img{raw_number}.png'
    cv2.imwrite(output_path, result)
    cv2.imwrite(backup_result_path, result)

    return jsonify({'result': True, 'img_after_edit': backup_result_path})

def find_file_in_directory(path, name):
    for root, dirs, files in os.walk(path):
        if name in files:
            return os.path.join(root, name)
    return None

def fetchFolder(root_dir, datePhoto, numOldPhoto):
    imgFile = f"img{numOldPhoto}.png"
    rawFile = f"img{numOldPhoto}.jpg"
    for foldername in os.listdir(root_dir):
        folder_path = os.path.join(root_dir, foldername)
        # Kiểm tra nếu là thư mục và tên thư mục chứa chuỗi tìm kiếm
        if os.path.isdir(folder_path) and datePhoto in foldername:
            print(f"Thư mục tìm thấy: {folder_path}")

            pathImg = find_file_in_directory(folder_path, imgFile)
            pathRaw = find_file_in_directory(os.path.join(folder_path, "RawFiles"), rawFile)
            print(pathImg)
            if pathImg != None:
                CapImagesPath = f"//PRINTSERVER1/CapImages/img{numOldPhoto}5.png"
                shutil.copy(pathImg, CapImagesPath)
            if pathRaw != None:
                RawFilePath = f"//PRINTSERVER1/CapImages/RawFiles/img{numOldPhoto}5.jpg"
                shutil.copy(pathRaw, RawFilePath)
            return True
    return False

@app.route('/find_old_photo', methods=["POST"])
def find_old_photo():
    numOldPhoto = request.json.get("img_number")
    date_string = request.json.get("datePhoto")

    date_obj = datetime.strptime(date_string, "%Y-%m-%d")

    datePhoto = date_string.replace(f"-0{date_obj.month}-", f"-{date_obj.month}-")

    root_directory_DiskC = f"//PRINTSERVER1/CapImages"
    root_directory = f"//PRINTSERVER1/CapImages_backup"

    found = fetchFolder(root_directory_DiskC, datePhoto, numOldPhoto)
    if not found:
        found = fetchFolder(root_directory, datePhoto, numOldPhoto)
        if not found:
            print(f"Không tìm thấy thư mục có tên chứa chuỗi '{datePhoto}'")
            return None 

    return jsonify({"result": "sucess"})

if __name__ == '__main__':
    app.run(debug=True)
