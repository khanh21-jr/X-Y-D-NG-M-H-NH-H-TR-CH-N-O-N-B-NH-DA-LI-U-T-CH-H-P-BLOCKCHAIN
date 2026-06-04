<h2 align="center">
<a href="https://dainam.edu.vn/vi/khoa-cong-nghe-thong-tin">
🎓 Faculty of Information Technology (DaiNam University)
</a>
</h2>

<h1 align="center">
 XÂY DỰNG MÔ HÌNH HỖ TRỢ CHẨN ĐOÁN BỆNH DA LIỄU TÍCH HỢP BLOCKCHAIN
</h1>

<div align="center">

<!-- Thay logo.png bằng ảnh của bạn trong repo -->
<img width="180" src="https://github.com/user-attachments/assets/77fe0fd1-2e55-4032-be3c-b1a705a1b574"/>

<br><br>

![Python](https://img.shields.io/badge/Python-3.x-blue?style=for-the-badge&logo=python)
![TensorFlow](https://img.shields.io/badge/TensorFlow-AI-orange?style=for-the-badge&logo=tensorflow)
![Blockchain](https://img.shields.io/badge/Blockchain-Ethereum-green?style=for-the-badge)
![University](https://img.shields.io/badge/DaiNam-University-orange?style=for-the-badge)

</div>

---


# 📖 1. Giới thiệu đề tài

XÂY DỰNG MÔ HÌNH HỖ TRỢ CHẨN ĐOÁN BỆNH DA LIỄU TÍCH HỢP BLOCKCHAIN là dự án kết hợp giữa Trí tuệ nhân tạo (AI) và Blockchain nhằm xây dựng hệ thống hỗ trợ nhận diện và chẩn đoán các bệnh da liễu từ hình ảnh, đồng thời lưu trữ thông tin chẩn đoán trên blockchain để đảm bảo tính minh bạch và khả năng truy xuất dữ liệu.

Hệ thống cho phép người dùng tải ảnh vùng da cần kiểm tra lên giao diện web, sau đó mô hình AI sẽ phân tích hình ảnh và đưa ra kết quả dự đoán bệnh lý da liễu. Các thông tin chẩn đoán có thể được ghi nhận lên blockchain nhằm đảm bảo tính toàn vẹn, minh bạch và hỗ trợ quản lý hồ sơ bệnh án điện tử.

### 🎯 Mục tiêu của đề tài

Xây dựng mô hình AI hỗ trợ chẩn đoán bệnh da liễu từ hình ảnh
Ứng dụng Deep Learning trong phân tích và xử lý ảnh y tế
Kết hợp Blockchain để lưu trữ dữ liệu chẩn đoán minh bạch
Xây dựng hệ thống web hỗ trợ người dùng và bác sĩ
Nâng cao khả năng nghiên cứu và ứng dụng công nghệ mới trong lĩnh vực y tế

---

# 🔍 2. Chức năng hệ thống

Chẩn đoán bệnh da liễu từ ảnh tải lên

✅ Phân loại nhiều loại bệnh da liễu khác nhau<br>
✅ Hiển thị kết quả dự đoán trực quan <br>
✅ Lưu lịch sử chẩn đoán<br>
✅ Kết nối Blockchain để xác thực dữ liệu<br>
✅ Quản lý thông tin bệnh nhân và kết quả chẩn đoán<br>

---

# ✨ 3. Tính năng nổi bật

## 🟢 Hệ thống AI

* Nhận diện bệnh da liễu bằng mô hình CNN
* Phân tích hình ảnh tự động
* Dự đoán nhanh chóng
* Độ chính xác cao
* Hỗ trợ mở rộng tập dữ liệu bệnh da liễu

## 🔴 Blockchain

* Lưu trữ thông tin chẩn đoán
* Tăng tính minh bạch và bảo mật dữ liệu
* Truy xuất nguồn gốc thông tin y tế
* Đảm bảo tính toàn vẹn hồ sơ bệnh án

## 🟡 Giao diện Web

* Thiết kế đơn giản, dễ sử dụng
* Tải ảnh trực tiếp từ thiết bị
* Hiển thị kết quả chẩn đoán trực quan
* Theo dõi lịch sử chẩn đoán

## 🔵 Quản lý dữ liệu

* Lưu trữ thông tin bệnh nhân
* Quản lý kết quả chẩn đoán
* Hỗ trợ truy vấn dữ liệu nhanh chóng
* Dễ dàng mở rộng và nâng cấp hệ thống

# ⚙️ 4. Công nghệ sử dụng

| Thành phần         | Công nghệ sử dụng        |
| ------------------ | ------------------------ |
| AI / Deep Learning | TensorFlow, CNN          |
| Xử lý ảnh y tế     | OpenCV                   |
| Backend            | Python, Flask            |
| Frontend           | HTML, CSS, JavaScript    |
| Blockchain         | Ethereum, Smart Contract |
| Ví Blockchain      | MetaMask                 |
| Cơ sở dữ liệu      | MongoDB                  |
| Quản lý mã nguồn   | GitHub                   |

---

# 📂 5. Cấu trúc dự án

```bash
chandoanbenhdalieu_blockchain/
│
├── dataset/
│   ├── acne/
│   ├── eczema/
│   ├── psoriasis/
│   ├── melanoma/
│
├── model/
│   ├── skin_disease_model.h5
│
├── blockchain/
│   ├── smart_contract.sol
│
├── static/
│   ├── css/
│   ├── js/
│   ├── images/
│
├── templates/
│   ├── index.html
│   ├── history.html
│
├── app.py
├── train.py
├── predict.py
├── blockchain.py
├── requirements.txt
├── README.md
```

# ▶️ 6. Cách cài đặt và chạy dự án

## 1️⃣ Clone dự án

```bash
git clone https://github.com/khanh21-jr/XAY-DUNG-MO-HINH-HO-TRO-CHUAN-DOAN-BENH-DA-LIEU-TICH-HOP-BLOCKCHAIN.git
```

```bash
cd XAY-DUNG-MO-HINH-HO-TRO-CHUAN-DOAN-BENH-DA-LIEU-TICH-HOP-BLOCKCHAIN
```

---

## 2️⃣ Cài đặt thư viện

```bash
pip install -r requirements.txt
```

Hoặc:

```bash
pip install tensorflow opencv-python flask pymongo numpy
```

---

## 3️⃣ Chạy hệ thống

```bash
python app.py
```

---

## 4️⃣ Truy cập giao diện

```text
http://127.0.0.1:5000
```

---

## 📌 Lưu ý

* Sử dụng Python 3.10 hoặc mới hơn
* Cài đặt đầy đủ thư viện trong requirements.txt
* Đảm bảo mô hình AI đã được huấn luyện
* Đảm bảo MongoDB đang hoạt động
* Nếu sử dụng Blockchain cần cài đặt MetaMask và kết nối mạng Ethereum phù hợp

---

# 🧠 7. Mô hình AI sử dụng

### CNN (Convolutional Neural Network)

Mô hình CNN được sử dụng để:

* Trích xuất đặc trưng từ hình ảnh da liễu
* Phân loại các loại bệnh da liễu
* Tăng độ chính xác trong chẩn đoán
* Hỗ trợ phát hiện sớm các dấu hiệu bất thường trên da

Quy trình hoạt động:

```text
Ảnh vùng da đầu vào
          ↓
Tiền xử lý ảnh
          ↓
Mô hình CNN
          ↓
Dự đoán bệnh da liễu
          ↓
Hiển thị kết quả
          ↓
Lưu Blockchain
```

---

# 🔗 8. Ứng dụng Blockchain

Blockchain được sử dụng để:

* Lưu trữ thông tin chẩn đoán
* Xác thực dữ liệu y tế
* Chống chỉnh sửa dữ liệu trái phép
* Đảm bảo tính minh bạch và toàn vẹn thông tin

Thông tin lưu trữ:

* Mã bệnh nhân
* Thời gian chẩn đoán
* Kết quả dự đoán bệnh
* Độ tin cậy của mô hình
* Mã giao dịch Blockchain (Transaction Hash)

---

# 🚀 9. Hướng phát triển tương lai

* Mở rộng tập dữ liệu bệnh da liễu
* Nâng cao độ chính xác của mô hình AI
* Tích hợp nhiều mô hình Deep Learning tiên tiến
* Hỗ trợ chẩn đoán thời gian thực từ camera
* Triển khai hệ thống trên nền tảng Cloud
* Phát triển ứng dụng Mobile
* Tích hợp hồ sơ bệnh án điện tử
* Kết nối Blockchain trong môi trường y tế thực tế

---

# 👨‍💻 10. Thông tin sinh viên

* **Họ và tên:** Nguyễn Tuấn Anh
* **Lớp:** CNTT 16-04
* **Khoa:** Công nghệ Thông tin
* **Trường:** Đại học Đại Nam

---

# 📌 11. Kết luận

Đề tài **Xây dựng mô hình hỗ trợ chẩn đoán bệnh da liễu tích hợp Blockchain** giúp sinh viên tiếp cận và nghiên cứu các công nghệ hiện đại như **Trí tuệ nhân tạo (AI), Deep Learning, Xử lý ảnh y tế và Blockchain**.

Thông qua dự án, sinh viên có cơ hội xây dựng một hệ thống hỗ trợ chẩn đoán bệnh da liễu hoàn chỉnh, từ việc xử lý dữ liệu hình ảnh, huấn luyện mô hình học sâu, phát triển ứng dụng web đến việc lưu trữ và xác thực dữ liệu trên blockchain nhằm nâng cao tính minh bạch và bảo mật thông tin y tế.

---

<div align="center">

### 🌟 Nếu thấy dự án hữu ích hãy cho một Star trên GitHub 🌟

⭐ ⭐ ⭐ ⭐ ⭐

**© 2026 Faculty of Information Technology - Dai Nam University**

</div>








