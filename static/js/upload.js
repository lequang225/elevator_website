(function () {
    const dropzone = document.getElementById('dropzone');
    if (!dropzone) return;

    const fileInput = document.getElementById('fileInput');
    const preview = document.getElementById('dropzonePreview');
    const content = document.getElementById('dropzoneContent');
    const previewImg = document.getElementById('previewImg');
    const removeBtn = document.getElementById('removeImg');
    const hiddenFilename = document.getElementById('imageFilename');

    const MAX_SIZE = 5 * 1024 * 1024;
    const ALLOWED = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp'];

    dropzone.addEventListener('click', (e) => {
        if (e.target === removeBtn || removeBtn.contains(e.target)) return;
        if (e.target.closest('.btn-crop')) return;
        fileInput.click();
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length) uploadFile(e.target.files[0]);
    });

    ['dragenter', 'dragover'].forEach(evt => {
        dropzone.addEventListener(evt, (e) => {
            e.preventDefault(); e.stopPropagation();
            dropzone.classList.add('dragover');
        });
    });

    ['dragleave', 'drop'].forEach(evt => {
        dropzone.addEventListener(evt, (e) => {
            e.preventDefault(); e.stopPropagation();
            if (evt === 'dragleave' && dropzone.contains(e.relatedTarget)) return;
            dropzone.classList.remove('dragover');
        });
    });

    dropzone.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        if (files.length) uploadFile(files[0]);
    });

    document.addEventListener('paste', (e) => {
        if (!dropzone.offsetParent) return;
        const items = e.clipboardData?.items;
        if (!items) return;
        for (const item of items) {
            if (item.type.startsWith('image/')) {
                uploadFile(item.getAsFile());
                break;
            }
        }
    });

    async function uploadFile(file) {
        if (!ALLOWED.includes(file.type)) {
            showToast('❌ Chỉ chấp nhận PNG, JPG, JPEG, GIF, WEBP', 'error');
            return;
        }
        if (file.size > MAX_SIZE) {
            showToast('❌ Ảnh vượt quá 5MB', 'error');
            return;
        }

        const reader = new FileReader();
        reader.onload = (e) => {
            previewImg.src = e.target.result;
            content.style.display = 'none';
            preview.style.display = 'flex';
        };
        reader.readAsDataURL(file);

        dropzone.classList.add('uploading');
        const fd = new FormData();
        fd.append('file', file);

        try {
            const res = await fetch('/api/upload_image', { method: 'POST', body: fd });
            const data = await res.json();
            if (data.success) {
                hiddenFilename.value = data.filename;
                previewImg.src = data.url;
                showToast('✅ Upload thành công');
            } else {
                resetDropzone();
                showToast('❌ ' + (data.error || 'Lỗi upload'), 'error');
            }
        } catch (err) {
            resetDropzone();
            showToast('❌ Lỗi kết nối', 'error');
        } finally {
            dropzone.classList.remove('uploading');
        }
    }

    removeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        resetDropzone();
    });

    function resetDropzone() {
        fileInput.value = '';
        hiddenFilename.value = '';
        previewImg.src = '';
        preview.style.display = 'none';
        content.style.display = 'block';
    }
})();
