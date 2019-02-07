document.addEventListener("DOMContentLoaded", function () {
    "use strict";
    if (new Resumable().support) {
        var dj = new DjangoResumable({
          onFileAdded: function(r, file, event, el, progress, filePath, fileName) {
            this.onFileAdded(r, file, event, el, progress, filePath, fileName);
            
            $('input[' + this.options.urlAttribute + ']').prop("disabled", true);
            $("#upload-label").addClass("disabled");

            let title_el = $("input[name='title']");
            if (title_el.val() == "")
            {
              let testfile = file.fileName;
              let dotIndex = testfile.lastIndexOf('.');
              if (dotIndex >= 1)
              {
                title_el.val(testfile.slice(0, dotIndex));
              }
              else
              {
                title_el.val(testfile);
              }
              //title_el.val(testfile.replace(/\..+$/, ''));
            }

            fileName.innerHTML = "Uploading";
          },

          onFileError: function(r, file, message, el) {
            this.onFileError(r, file, message, el);
            $('input[' + this.options.urlAttribute + ']').prop("disabled", false);
            $("#upload-label").removeClass("disabled");
          },

          onFileSuccess: function(r, file, message, el, progress, filePath, fileName) {
            this.onFileSuccess(r, file, message, el, progress, filePath, fileName);
          },
        });
    }
});
