// Chỉnh sửa sản phẩm inline
document.querySelectorAll('[data-editable="true"]').forEach(el => {
    el.classList.add('editable');
    el.title = 'Nhấn để chỉnh sửa';

    el.addEventListener('click', function () {
        if (el.dataset.editing === 'true') return;
        el.dataset.editing = 'true';

        const field = el.dataset.field;
        const id = el.dataset.id;
        const type = el.dataset.type || 'text';
        const oldValue = type === 'number'
            ? parseFloat(el.textContent.replace(/[^\d.]/g, ''))
            : el.textContent.trim();
        const original = el.textContent;

        let input;
        if (field === 'description') {
            input = document.createElement('textarea');
            input.rows = 3;
        } else {
            input = document.createElement('input');
            input.type = type === 'number' ? 'number' : 'text';
        }
        input.value = oldValue;
        input.className = 'inline-edit-input';

        el.textContent = '';
        el.appendChild(input);
        input.focus();
        input.select();

        const save = async () => {
            let newValue = input.value.trim();
            if (field === 'price') newValue = parseFloat(newValue) || 0;

            if (newValue !== '' && String(newValue) !== String(oldValue)) {
                try {
                    const res = await fetch(`/api/product/${id}`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ [field]: newValue })
                    });
                    if (res.ok) {
                        if (field === 'price') {
                            el.textContent = Number(newValue).toLocaleString('vi-VN') + ' VNĐ';
                        } else {
                            el.textContent = newValue;
                        }
                        showToast('✅ Đã lưu');
                    } else {
                        el.textContent = original;
                        showToast('❌ Lỗi', 'error');
                    }
                } catch (err) {
                    el.textContent = original;
                    showToast('❌ Lỗi kết nối', 'error');
                }
            } else {
                el.textContent = original;
            }
            el.dataset.editing = 'false';
        };

        const cancel = () => {
            el.textContent = original;
            el.dataset.editing = 'false';
        };

        input.addEventListener('blur', save);
        input.addEventListener('keydown', e => {
            if (e.key === 'Enter' && field !== 'description') { e.preventDefault(); input.blur(); }
            if (e.key === 'Escape') { input.removeEventListener('blur', save); cancel(); }
        });
    });
});
