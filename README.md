# 🛗 Website Công Ty Thang Máy

Website quản trị công ty thang máy với đầy đủ tính năng: quản lý sản phẩm, dự án, slider, upload ảnh (drag & drop, crop), quản lý user, lịch sử hoạt động, cấu hình giao diện.

## 🚀 Cài đặt

```bash
# Tạo cấu trúc
mkdir -p elevator_website/{static/{css,js,uploads},templates}
cd elevator_website

# Tạo venv
python3 -m venv venv
source venv/bin/activate

# Cài thư viện
pip install -r requirements.txt

# Chạy
python3 app.py
