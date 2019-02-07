document.addEventListener("DOMContentLoaded", function () {
    "use strict";
    if (new Resumable().support) {
        var dj = new DjangoResumable({
          onFileAdded: function(r, file, event, el, progress, filePath, fileName) {
            this.onFileAdded(r, file, event, el, progress, filePath, fileName);
            fileName.innerHTML = "Uploading";
            $('input[' + this.options.urlAttribute + ']').prop("disabled", true);
            $("#upload-label").addClass("disabled");
          },

          onFileError: function(r, file, message, el) {
            this.onFileError(r, file, message, el);
            $('input[' + this.options.urlAttribute + ']').prop("disabled", false);
            $("#upload-label").removeClass("disabled");
          },

          onFileSuccess: function(r, file, message, el, progress, filePath, fileName) {
            this.onFileSuccess(r, file, message, el, progress, filePath, fileName);
            let title_el = $("input[name='title']");
            if (title_el.val() == "")
            {
              let testfile = fileName.innerHTML.replace();
              title_el.val(testfile.replace(/\..+$/, ''));
            }
          },
        });
    }
});
