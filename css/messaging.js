window.onload = scrollSet();
function scrollSet()
{
	var objDiv = document.getElementById("chatlog");
	objDiv.scrollTop = objDiv.scrollHeight;
}

window.onload = setupRefresh;
function setupRefresh()
{
	setInterval(refreshBlock,1000);
	// setInterval(refreshOnline,15000);
	// setInterval(scrollSet, 100);
}

function refreshBlock()
{
	//$('#chatlog').load("showMessages");
    var user = $("#sendButton").val();
	$.get("./showMessages",{username: user}, function(data)
	{
	    var scrollAmount = $('#chatlog').scrollTop();
		var replacement = $(data).find('#chatlog');
		$('#chatlog').replaceWith(replacement);
		$('#chatlog').scrollTop(scrollAmount);
	});
}

// function refreshOnline()
// {
// 	//$('#chatlog').load("showMessages");
// 	$.get("showMessages", function(data)
// 	{
// 		var replacement = $(data).find('#online');
// 		$('#online').replaceWith(replacement);
//
// 	});
// }