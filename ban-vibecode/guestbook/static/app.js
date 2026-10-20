// Các hiệu ứng phía trình duyệt. Trang vẫn dùng được đầy đủ khi tắt JavaScript.
// Mọi nội dung người dùng nhập đều được gán qua textContent (không dùng innerHTML) để tránh XSS.

(function () {
    "use strict";

    // ---------- Sáng / tối ----------
    const themeToggle = document.getElementById("theme-toggle");
    if (themeToggle) {
        themeToggle.addEventListener("click", function () {
            const root = document.documentElement;
            const systemDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
            const current = root.dataset.theme || (systemDark ? "dark" : "light");
            const next = current === "dark" ? "light" : "dark";
            root.dataset.theme = next;
            try { localStorage.setItem("theme", next); } catch (e) {}
        });
    }

    // ---------- Toast: tự ẩn sau vài giây ----------
    const TOAST_DURATION = 4500;
    document.querySelectorAll(".toast").forEach(function (toast) {
        const dismiss = function () {
            if (toast.classList.contains("is-leaving")) return;
            toast.classList.add("is-leaving");
            setTimeout(function () { toast.remove(); }, 300);
        };
        toast.style.setProperty("--toast-duration", TOAST_DURATION + "ms");
        toast.classList.add("is-timed");
        toast.querySelector(".toast-close").addEventListener("click", dismiss);
        setTimeout(dismiss, TOAST_DURATION);
    });

    // ---------- Hộp xác nhận trước khi xóa ----------
    const dialog = document.getElementById("confirm-dialog");
    let pendingForm = null;
    if (dialog && typeof dialog.showModal === "function") {
        document.querySelectorAll("form[data-confirm]").forEach(function (form) {
            form.addEventListener("submit", function (event) {
                event.preventDefault();
                pendingForm = form;
                document.getElementById("confirm-text").textContent = form.dataset.confirm;
                dialog.returnValue = "";
                dialog.showModal();
            });
        });
        dialog.addEventListener("close", function () {
            // form.submit() không kích hoạt lại sự kiện submit nên không bị hỏi lặp
            if (dialog.returnValue === "confirm" && pendingForm) pendingForm.submit();
            pendingForm = null;
        });
        // Bấm ra ngoài hộp thoại thì đóng
        dialog.addEventListener("click", function (event) {
            if (event.target === dialog) dialog.close("cancel");
        });
    }

    // ---------- Tìm kiếm lời nhắn ----------
    const search = document.getElementById("search");
    if (search) {
        const notes = document.querySelectorAll("#notes .note");
        const noResults = document.getElementById("no-results");
        search.addEventListener("input", function () {
            const keyword = search.value.trim().toLowerCase();
            let shown = 0;
            notes.forEach(function (note) {
                const match = note.dataset.search.includes(keyword);
                note.classList.toggle("is-hidden", !match);
                if (match) shown++;
            });
            noResults.hidden = shown > 0;
        });
        search.addEventListener("keydown", function (event) {
            if (event.key === "Escape") {
                search.value = "";
                search.dispatchEvent(new Event("input"));
                search.blur();
            }
        });
        // Phím "/" để nhảy tới ô tìm kiếm
        document.addEventListener("keydown", function (event) {
            const typing = /^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName);
            if (event.key === "/" && !typing && !event.ctrlKey && !event.metaKey) {
                event.preventDefault();
                search.focus();
            }
        });
    }

    // ---------- Trang viết lời nhắn: đếm ký tự, xem trước, Ctrl+Enter ----------
    const form = document.getElementById("compose-form");
    if (form) {
        const nameInput = document.getElementById("name");
        const messageInput = document.getElementById("message");
        const preview = document.getElementById("preview");
        const previewName = document.getElementById("preview-name");
        const previewMessage = document.getElementById("preview-message");
        const previewAvatar = document.getElementById("preview-avatar");

        const updateCounter = function (input) {
            const counter = form.querySelector('[data-counter-for="' + input.id + '"]');
            const max = Number(input.getAttribute("maxlength"));
            counter.textContent = input.value.length + "/" + max;
            counter.classList.toggle("is-near", input.value.length >= max * 0.9);
        };

        const setText = function (element, value) {
            const text = value.trim();
            element.textContent = text || element.dataset.placeholder;
            element.classList.toggle("is-placeholder", !text);
        };

        const updatePreview = function () {
            const name = nameInput.value.trim();
            setText(previewName, nameInput.value);
            setText(previewMessage, messageInput.value);
            previewAvatar.textContent = initials(name) || "?";
            // Cùng công thức với Entry.hue bên Python nên màu xem trước khớp với màu thật
            preview.style.setProperty("--hue", name ? crc32(name.toLowerCase()) % 360 : 250);
        };

        [nameInput, messageInput].forEach(function (input) {
            input.addEventListener("input", function () {
                updateCounter(input);
                updatePreview();
            });
        });
        updatePreview();

        form.addEventListener("keydown", function (event) {
            if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
                event.preventDefault();
                form.requestSubmit();
            }
        });
    }

    // "Nguyễn Văn An" -> "NA", "An" -> "A" (giống Entry.initials)
    function initials(name) {
        const words = name.split(/\s+/).filter(Boolean);
        if (words.length >= 2) {
            return (Array.from(words[0])[0] + Array.from(words[words.length - 1])[0]).toUpperCase();
        }
        return (Array.from(name)[0] || "").toUpperCase();
    }

    // CRC-32 trên các byte UTF-8, cho kết quả giống zlib.crc32 của Python
    function crc32(text) {
        let crc = 0xffffffff;
        for (const byte of new TextEncoder().encode(text)) {
            crc ^= byte;
            for (let k = 0; k < 8; k++) crc = (crc >>> 1) ^ (0xedb88320 & -(crc & 1));
        }
        return (crc ^ 0xffffffff) >>> 0;
    }
})();
