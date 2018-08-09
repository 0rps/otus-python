document.addEventListener("DOMContentLoaded",
function () {
    var search = document.getElementById('search_input');

    function key_up_event(event) {
        if (event.keyCode === 13) {
            var value = search.value;
            if (value.length !== 0) {
                window.location.href = "/qa/search?" + 'q=' + encodeURIComponent(value);
            }
        }
    }

    search.onkeyup = key_up_event;
});
