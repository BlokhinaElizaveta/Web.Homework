function openSection(sectionName) {
	var i, tabcontent, tablinks;
	tabcontent = document.getElementsByClassName("content");
	for (i = 0; i < tabcontent.length; i++) {
		tabcontent[i].style.display = "none";
	}
	tablinks = document.getElementsByClassName("section");
	for (i = 0; i < tablinks.length; i++) {
		tablinks[i].className = tablinks[i].className.replace(" active", "");
	}
	document.getElementById(sectionName).style.display = "block";
	currentSection = sectionName;
	document.getElementsByClassName(currentSection)[0].className += " active";
	document.getElementById("Comment").style.display = "none";
	document.getElementById("Slides").style.display = "none";
	document.getElementById("Counter").style.display = "block";
}

var currentSection;
var currentIndex;
var count = document.getElementsByClassName("demo").length;
var nextImage;

function openSlide(index) {
	currentIndex = index;
	var gallery = document.getElementById("Photo");
	gallery.style.display = "none";
	var slide = document.getElementById("Slides");
	slide.style.display = "block";
	document.getElementById("Counter").style.display = "none";
	currentSection = "Slides";
	changeSlide();
}

function changeCurrentIndex(shift) {
	if (0 < currentIndex + shift && currentIndex + shift <= count) {
		currentIndex += shift;
		updateHistory();
	}
	if (nextImage && shift === 1) {
		if (nextImage.complete)
			insertImage();
		else
			changeSlide();
	}
	else
		changeSlide();
	loadNextImage();
}

function changeSlide() {
	var image = document.getElementById("currentSlide");
	image.src = "static/images/photo" + currentIndex + ".jpg";
	document.getElementById("numberPhoto").innerHTML = currentIndex + "/" + count;
	if (!image.complete) {
		image.style.display = "none";
		document.getElementById("loading").style.display = "block";
	}
	image.addEventListener('load', showImage);
}

function showImage() {
	var image = document.getElementById("currentSlide");
	image.style.display = "block";
	document.getElementById("loading").style.display = "none";
	saveCurrentIndex();
	load_comment();
}

function closeSlide() {
	var gallery = document.getElementById("Photo");
	gallery.style.display = "block";
	var slide = document.getElementById("Slides");
	slide.style.display = "none";
	document.getElementById("Counter").style.display = "block";
}

function updateHistory() {
	try {
		history.pushState(currentIndex, null, `#photo${currentIndex}.html`);
	} catch (err) { }
}

function keyboardManagement(event) {
	event = event || window.event;
	var charCode = event.keyCode || event.which;
	if (currentSection === "Slides") {
		if (charCode === 27)
			closeSlide();
		if (charCode === 39)
			changeCurrentIndex(1);
		if (charCode === 37)
			changeCurrentIndex(-1);
	}
	if (currentSection === "Slides" || currentSection === "Photo") {
		if (charCode === 112) {
			event.preventDefault();
			var help = window.open("about:blank", "Справка");
			help.document.write('<!DOCTYPE html><html><head><meta charset="utf-8" /><title>Справка</title></head><body><h1>Помощь по использованию фотогалереи</h1><p> &rarr; - переход к следующей фотографии</p> <p> &larr; - переход к предыдущей фотографии</p><p> Esc - закрыть фотографию</p></body></html>');
		}
	}
}

function loadNextImage() {
	if (currentIndex < count) {
		var nextIndex = currentIndex + 1;
		nextImage = document.createElement("img");
		nextImage.src = "static/images/photo" + nextIndex + ".jpg";
		nextIndex.alt = "photo";
		nextImage.id = "currentSlide";
	}
}

function insertImage() {
	var div = document.getElementsByClassName("modal-slide")[0];
	var oldImage = document.getElementById("currentSlide");
	div.removeChild(oldImage);
	div.appendChild(nextImage);
	nextImage = null;
	document.getElementById("numberPhoto").innerHTML = currentIndex + "/" + count;
	showImage();
}

window.onbeforeunload = function () {
	sessionStorage.setItem("section", currentSection);
	sessionStorage.setItem("numberPhoto", currentIndex);
};

window.onload = function () {
	currentSection = sessionStorage.getItem("section");
	if (currentSection == null)
		currentSection = "Attraction";

	if (currentSection !== "Slides")
		openSection(currentSection);
	else {
		openSection("Photo");
		currentIndex = parseInt(sessionStorage.getItem("numberPhoto"));
		openSlide(currentIndex);
	}
}

window.onpopstate = function (e) {
	if (e.state != null) {
		currentIndex = e.state;
		openSlide(currentIndex);
	}
}

function getCookie(name) {
	var matches = document.cookie.match(new RegExp(
		"(?:^|; )" + name.replace(/([\.$?*|{}\(\)\[\]\\\/\+^])/g, '\\$1') + "=([^;]*)"
	));
	return matches ? decodeURIComponent(matches[1]) : undefined;
}

function setCookie(name) {
	var value = currentIndex;
	var updatedCookie = name + "=" + value;
	document.cookie = updatedCookie;
	console.log(document.cookie);
}

function updateBackgroungImage() {
	var header = document.getElementById("header");
	var number = getCookie("backgroundImage");
	var nameImage = "static/images/photo" + number + ".jpg";
	var url = `url("${nameImage}")`;
	header.style.backgroundImage = url;
}

function addComment() {
	var slide = document.getElementById("Slides");
	slide.style.display = "none";
	var commentForm = document.getElementById("Comment");
	commentForm.style.display = "block";
}

function saveCurrentIndex() {
	var xhr = new XMLHttpRequest();
	var body = 'index=' + encodeURIComponent(currentIndex);
	xhr.open("POST", '/save_index', false);
	xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
	xhr.send(body);
}

function load_comment() {
	var xhr = new XMLHttpRequest();
	xhr.open('GET', '/load_comment', false);
	xhr.send();
	if (xhr.status !== 200) {
		console.log(xhr.status + ': ' + xhr.statusText);
	} else {
		var list = document.getElementById("temp");
		if (list)
			list.parentNode.removeChild(list);
		var div = document.createElement('div');
		div.id = 'temp';
		div.innerHTML = xhr.responseText;
		document.getElementById('modal-slide').appendChild(div);
	}
}
