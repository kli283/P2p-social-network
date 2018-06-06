window.onload = scrollSet();
// This function scrolls to the bottom when the page is loaded
function scrollSet()
{
	var objDiv = document.getElementById("chatlog");
	objDiv.scrollTop = objDiv.scrollHeight;
}

window.onload = setupRefresh;
function setupRefresh()
{
	setInterval(refreshBlock,1000);
	setInterval(refreshOnline,15000);
}
// This function refreshes parts of the page while keeping the scroll at the current position
function refreshBlock()
{
    var user = $("#sendButton").val();
	$.get("./showMessages",{username: user}, function(data)
	{
	    var scrollAmount = $('#chatlog').scrollTop();
		var replacement = $(data).find('#chatlog');
		$('#chatlog').replaceWith(replacement);
		$('#chatlog').scrollTop(scrollAmount);
	});
}

function refreshOnline()
{
	var user = $("#sendButton").val();
	$.get("./showMessages",{username: user}, function(data)
	{
		var replacement = $(data).find('#online');
		$('#online').replaceWith(replacement);

	});
}