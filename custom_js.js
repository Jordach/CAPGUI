function gradioApp() {
	const elems = document.getElementsByTagName('gradio-app');
	const elem = elems.length == 0 ? document : elems[0];

	if (elem !== document) {
		elem.getElementById = function(id) {
			return document.getElementById(id);
		};
	}
	return elem.shadowRoot ? elem.shadowRoot : elem;
}

function get_uiCurrentTab() {
	return gradioApp().querySelector('.tabs > .tab-nav > button.selected');
}

function get_tab_window() {
	return gradioApp().querySelector('.tabs > .tabitem[id^=tab_]:not([style*="display: none"])');
}

document.addEventListener('keydown', function(e) {
	const isEnter = e.key === 'Enter' || e.keyCode === 13;
	const isCtrlKey = e.metaKey || e.ctrlKey;
	const isAltKey = e.altKey;
	const isEsc = e.key === 'Escape';
	
	const generateButton = get_tab_window().querySelector('#topbar > #buttons > button[id^=generate_]');
	if (isCtrlKey && isEnter) {
		e.preventDefault();
		generateButton.click();
	}
})