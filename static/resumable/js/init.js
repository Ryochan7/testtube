document.addEventListener("DOMContentLoaded", function () {
    "use strict";
    if (new Resumable().support) {
        var dj = new DjangoResumable();
    }
});
