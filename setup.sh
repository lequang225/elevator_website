#!/bin/bash
# Script tạo nhanh cấu trúc file
echo "Đang tạo cấu trúc..."

mkdir -p static/{css,js,uploads} templates

# Tạo file rỗng
touch requirements.txt app.py
touch templates/{base,index,products,add_product,edit_product,contact,login,admin_dashboard,change_password,user_list,user_add,activity_log}.html
touch static/js/{main,admin,upload,gallery}.js
touch static/css/style.css
touch static/uploads/.gitkeep
touch README.md .gitignore

echo "✅ Đã tạo xong các file rỗng!"
echo ""
echo "📁 Cấu trúc:"
find . -type f -not -path './.git/*' | sort
