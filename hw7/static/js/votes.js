function _getCookie(name) {
  var matches = document.cookie.match(new RegExp(
    "(?:^|; )" + name.replace(/([\.$?*|{}\(\)\[\]\\\/\+^])/g, '\\$1') + "=([^;]*)"
  ));
  return matches ? decodeURIComponent(matches[1]) : undefined;
}

function _send_query_with_reload(url, data) {
    var formData = new FormData();
    for (var key in data) {
        formData.append(key, data[key]);
    }
    formData.append('csrfmiddlewaretoken', _getCookie('csrftoken'));

    var xhr = new XMLHttpRequest();
    xhr.open("POST", url);

    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4 && xhr.status === 200) {
            window.location.href = window.location.href
        }
    };
    xhr.send(formData);
}


function starAnswer(aId) {
    _send_query_with_reload("/qa/answer/" + aId + '/star', {});
}

function unstarAnswer(aId) {
    _send_query_with_reload("/qa/answer/" + aId + '/unstar', {});
}

function cancelVoteQuestion(qId) {
    var url = "/qa/question/" + qId + '/unvote';
    _send_query_with_reload(url, {})
}

function cancelVoteAnswer(aId) {
    _send_query_with_reload("/qa/answer/" + aId + '/unvote', {});
}

function voteQuestion(qId, isUp) {
    var like = isUp ? 1 : -1;
    var url = "/qa/question/" + qId + '/vote';
    _send_query_with_reload(url, {'like': like});
}

function voteAnswer(aId, isUp) {
    var like = isUp ? 1 : -1;
    var url = "/qa/answer/" + aId + '/vote?';
    _send_query_with_reload(url, {'like': like});
}
