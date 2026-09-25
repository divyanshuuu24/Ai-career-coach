// =====================================================
// AI Career Coach — Global front-end behavior
// =====================================================

document.addEventListener("DOMContentLoaded", () => {
  // Fade-in animation for elements marked with .animate-on-scroll
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("card-hover-fade");
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.15 });

  document.querySelectorAll(".animate-on-scroll").forEach((el) => observer.observe(el));

  // Auto-dismiss flash alerts after 5 seconds
  document.querySelectorAll(".alert").forEach((alert) => {
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      bsAlert.close();
    }, 5000);
  });

  // Bootstrap client-side form validation (adds .was-validated on submit)
  document.querySelectorAll("form.needs-validation").forEach((form) => {
    form.addEventListener("submit", (event) => {
      if (!form.checkValidity()) {
        event.preventDefault();
        event.stopPropagation();
      }
      form.classList.add("was-validated");
    });
  });

  // Password confirmation live check on the register page
  const pwd = document.getElementById("password");
  const confirmPwd = document.getElementById("confirm_password");
  if (pwd && confirmPwd) {
    const validateMatch = () => {
      confirmPwd.setCustomValidity(pwd.value !== confirmPwd.value ? "Passwords do not match" : "");
    };
    pwd.addEventListener("input", validateMatch);
    confirmPwd.addEventListener("input", validateMatch);
  }

  // Resume upload dropzone interactivity
  const dropzone = document.getElementById("uploadDropzone");
  const fileInput = document.getElementById("resume_file");
  const fileLabel = document.getElementById("fileNameLabel");
  if (dropzone && fileInput) {
    dropzone.addEventListener("click", () => fileInput.click());
    ["dragenter", "dragover"].forEach((evt) =>
      dropzone.addEventListener(evt, (e) => { e.preventDefault(); dropzone.classList.add("dragover"); })
    );
    ["dragleave", "drop"].forEach((evt) =>
      dropzone.addEventListener(evt, (e) => { e.preventDefault(); dropzone.classList.remove("dragover"); })
    );
    dropzone.addEventListener("drop", (e) => {
      if (e.dataTransfer.files.length) {
        fileInput.files = e.dataTransfer.files;
        if (fileLabel) fileLabel.textContent = e.dataTransfer.files[0].name;
      }
    });
    fileInput.addEventListener("change", () => {
      if (fileInput.files.length && fileLabel) fileLabel.textContent = fileInput.files[0].name;
    });
  }
});
