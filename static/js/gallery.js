(function () {
    const MAX_SIZE = 5 * 1024 * 1024;
    const ALLOWED = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp'];

    const dropzone = document.getElementById('galleryDropzone');
    const fileInput = document.getElementById('galleryInput');
    const preview = document.getElementById('galleryPreview');

    if (dropzone && fileInput && preview) {
        dropzone.addEventListener('click', () => fileInput.click());

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length) handleFiles(e.target.files);
            fileInput.value = '';
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
            if (files.length) handleFiles(files);
        });

        async function handleFiles(files) {
            const validFiles = [];
            for (const f of files) {
                if (!ALLOWED.includes(f.type)) {
                    showToast(`❌ "${f.name}" không hợp lệ`, 'error');
                    continue;
                }
                if (f.size > MAX_SIZE) {
                    showToast(`❌ "${f.name}" > 5MB`, 'error');
                    continue;
                }
                validFiles.push(f);
            }
            if (!validFiles.length) return;

            const placeholders = validFiles.map(f => {
                const div = document.createElement('div');
                div.className = 'gallery-preview-item uploading';
                div.innerHTML = `<div class="upload-spinner"></div><small>${f.name}</small>`;
                preview.appendChild(div);
                return div;
            });

            const fd = new FormData();
            validFiles.forEach(f => fd.append('files', f));

            try {
                const res = await fetch('/api/upload_multiple', { method: 'POST', body: fd });
                const data = await res.json();

                if (data.success) {
                    data.files.forEach((file, idx) => {
                        const ph = placeholders[idx];
                        if (file.success) {
                            ph.classList.remove('uploading');
                            ph.innerHTML = `
                                <img src="${file.url}">
                                <input type="hidden" name="gallery_images[]" value="${file.filename}">
                                <input type="hidden" name="new_gallery_images[]" value="${file.filename}">
                                <button type="button" class="gallery-remove">✕</button>
                            `;
                            ph.querySelector('.gallery-remove').onclick = () => ph.remove();
                        } else {
                            ph.remove();
                        }
                    });
                    const ok = data.files.filter(f => f.success).length;
                    if (ok) showToast(`✅ Đã upload ${ok} ảnh`);
                } else {
                    placeholders.forEach(p => p.remove());
                    showToast('❌ ' + (data.error || 'Lỗi upload'), 'error');
                }
            } catch (err) {
                placeholders.forEach(p => p.remove());
                showToast('❌ Lỗi kết nối', 'error');
            }
        }
    }
})();

// CROP
let cropper = null;
(function () {
    const cropModal = document.getElementById('cropModal');
    const cropImage = document.getElementById('cropImage');
    const cropClose = document.getElementById('cropClose');
    const cropCancel = document.getElementById('cropCancel');
    const cropApply = document.getElementById('cropApply');
    const btnCrop = document.getElementById('btnCrop');

    if (!cropModal || !cropImage) return;

    if (btnCrop) {
        btnCrop.addEventListener('click', (e) => {
            e.stopPropagation();
            const previewImg = document.getElementById('previewImg');
            if (!previewImg || !previewImg.src) return;
            openCropModal(previewImg.src);
        });
    }

    function openCropModal(src) {
        cropImage.src = src;
        cropModal.classList.add('show');
        document.body.style.overflow = 'hidden';
        cropImage.onload = () => {
            if (cropper) cropper.destroy();
            cropper = new Cropper(cropImage, {
                aspectRatio: 1, viewMode: 1, autoCropArea: 0.9,
                responsive: true, background: false
            });
        };
    }

    function closeCropModal() {
        cropModal.classList.remove('show');
        document.body.style.overflow = '';
        if (cropper) { cropper.destroy(); cropper = null; }
    }

    cropClose.addEventListener('click', closeCropModal);
    cropCancel.addEventListener('click', closeCropModal);

    document.querySelectorAll('.ratio-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.ratio-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const ratio = parseFloat(btn.dataset.ratio);
            if (cropper) cropper.setAspectRatio(ratio);
        });
    });

    cropApply.addEventListener('click', async () => {
        if (!cropper) return;
        const canvas = cropper.getCroppedCanvas({ maxWidth: 1600, maxHeight: 1600, imageSmoothingQuality: 'high' });
        const croppedDataUrl = canvas.toDataURL('image/png');
        cropApply.disabled = true;
        cropApply.textContent = '⏳ Đang lưu...';

        try {
            const res = await fetch('/api/upload_cropped', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image: croppedDataUrl })
            });
            const data = await res.json();
            if (data.success) {
                document.getElementById('previewImg').src = data.url;
                document.getElementById('imageFilename').value = data.filename;
                document.getElementById('dropzoneContent').style.display = 'none';
                document.getElementById('dropzonePreview').style.display = 'flex';
                showToast('✅ Đã crop & lưu');
                closeCropModal();
            } else {
                showToast('❌ ' + (data.error || 'Lỗi'), 'error');
            }
        } catch (err) {
            showToast('❌ Lỗi kết nối', 'error');
        } finally {
            cropApply.disabled = false;
            cropApply.textContent = '✂️ Crop & Lưu';
        }
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && cropModal.classList.contains('show')) closeCropModal();
    });
})();
