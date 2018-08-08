document.addEventListener("DOMContentLoaded",
    function () {
    var search = document.getElementById('search_input');

    function key_up_event(event) {
        if (event.keyCode === 13) {
            var value = search.value;
            if (value.length !== 0 ) {
                window.location.href = "/qa/search?" + 'q=' + encodeURIComponent(value);
            }
        }
    }

    search.onkeyup = key_up_event;
});

function starAnswer(aId) {

}

function unstarAnswer(aId) {

}

function cancelVoteQuestion(qId) {

}

function cancelVoteAnswer(aId) {

}

function voteQuestion(qId, isUp) {
    console.log(qId, isUp);
}

function voteAnswer(aId, isUp) {
    var like;
    if (isUp) {
        like = 1;
    } else {
        like = -1;
    }

    window.location.href = "/qa/answer/" + aId + '/vote?' + 'like=' + encodeURIComponent(like);
}