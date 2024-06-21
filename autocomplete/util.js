function parseCSV_tac(str) {
    const arr = [];
    let quote = false;  // 'true' means we're inside a quoted field

    // Iterate over each character, keep track of current row and column (of the returned array)
    for (let row = 0, col = 0, c = 0; c < str.length; c++) {
        let cc = str[c], nc = str[c + 1];        // Current character, next character
        arr[row] = arr[row] || [];             // Create a new row if necessary
        arr[row][col] = arr[row][col] || '';   // Create a new column (start with empty string) if necessary

        // If the current character is a quotation mark, and we're inside a
        // quoted field, and the next character is also a quotation mark,
        // add a quotation mark to the current column and skip the next character
        if (cc === '"' && quote && nc === '"') {
            arr[row][col] += cc;
            ++c;
            continue;
        }

        // If it's just one quotation mark, begin/end quoted field
        if (cc === '"') {
            quote = !quote;
            continue;
        }

        // If it's a comma and we're not in a quoted field, move on to the next column
        if (cc === ',' && !quote) {
            ++col;
            continue;
        }

        // If it's a newline (CRLF), skip the next character and move on to the next row and move to column 0 of that new row
        if (cc === '\r' && nc === '\n') {
            ++row;
            col = 0;
            ++c;
            quote = false;
            continue;
        }

        // If it's a newline (LF or CR) move on to the next row and move to column 0 of that new row
        if (cc === '\n') {
            ++row;
            col = 0;
            quote = false;
            continue;
        }
        if (cc === '\r') {
            ++row;
            col = 0;
            quote = false;
            continue;
        }

        // Otherwise, append the current character to the current column
        arr[row][col] += cc;
    }
    return arr;
}

// Load file
async function readFile_tac(filePath, json = false, cache = false) {
    if (!cache)
        filePath += `?${new Date().getTime()}`;

    let response = await fetch(`file=${filePath}`);

    if (response.status !== 200) {
        console.error(`Error loading file "${filePath}": ` + response.status, response.statusText);
        return null;
    }

    if (json)
        return await response.json();
    else
        return await response.text();
}

// Load CSV
async function loadCSV_tac(path) {
    let text = await readFile_tac(path);
    if (!text) return [];
    return parseCSV_tac(text);
}

function escapeRegExp(string, wildcardMatching = false) {
    if (wildcardMatching) {
        // Escape all characters except asterisks and ?, which should be treated separately as placeholders.
        return string.replace(/[-[\]{}()+.,\\^$|#\s]/g, '\\$&').replace(/\*/g, '.*').replace(/\?/g, '.');
    }
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); // $& means the whole matched string
}

function escapeHTML(unsafeText) {
    let div = document.createElement('div');
    div.textContent = unsafeText;
    return div.innerHTML;
}

function filter_tags_tac(allTags, tagword, searchByAlias) {
    let results = [];
    // Create escaped search regex with support for * as a start placeholder
    let searchRegex;
    if (tagword.startsWith("*")) {
        tagword = tagword.slice(1);
        searchRegex = new RegExp(`${escapeRegExp(tagword)}`, 'i');
    } else {
        searchRegex = new RegExp(`(^|[^a-zA-Z])${escapeRegExp(tagword)}`, 'i');
    }

    // Both normal tags and aliases/translations are included depending on the config
    let baseFilter = (x) => x[0].toLowerCase().search(searchRegex) > -1;
    let aliasFilter = (x) => x[3] && x[3].toLowerCase().search(searchRegex) > -1;

    let fil;
    if (searchByAlias)
        fil = (x) => baseFilter(x) || aliasFilter(x);
    else
        fil = (x) => baseFilter(x);

    // Add final results
    allTags.filter(fil).forEach(t => {
        results.push({
            tag: t[0].trim(),
            category: t[1],
            count: t[2],
            aliases: t[3]
        });
    });

    return results;
}

// Caret position calculation from @component/textarea-caret-position
// We'll copy the properties below into the mirror div.
// Note that some browsers, such as Firefox, do not concatenate properties
// into their shorthand (e.g. padding-top, padding-bottom etc. -> padding),
// so we have to list every single property explicitly.
const properties = [
    'direction',  // RTL support
    'boxSizing',
    'width',  // on Chrome and IE, exclude the scrollbar, so the mirror div wraps exactly as the textarea does
    'height',
    'overflowX',
    'overflowY',  // copy the scrollbar for IE

    'borderTopWidth',
    'borderRightWidth',
    'borderBottomWidth',
    'borderLeftWidth',
    'borderStyle',

    'paddingTop',
    'paddingRight',
    'paddingBottom',
    'paddingLeft',

    // https://developer.mozilla.org/en-US/docs/Web/CSS/font
    'fontStyle',
    'fontVariant',
    'fontWeight',
    'fontStretch',
    'fontSize',
    'fontSizeAdjust',
    'lineHeight',
    'fontFamily',

    'textAlign',
    'textTransform',
    'textIndent',
    'textDecoration',  // might not make a difference, but better be safe

    'letterSpacing',
    'wordSpacing',

    'tabSize',
    'MozTabSize'

];

const isBrowser = (typeof window !== 'undefined');
const isFirefox = (isBrowser && window.mozInnerScreenX != null);

function getCaretCoordinates(element, position, options) {
    if (!isBrowser) {
        throw new Error('textarea-caret-position#getCaretCoordinates should only be called in a browser');
    }

    const debug = options && options.debug || false;
    if (debug) {
        const el = document.querySelector('#input-textarea-caret-position-mirror-div');
        if (el) el.parentNode.removeChild(el);
    }

    // The mirror div will replicate the textarea's style
    const div = document.createElement('div');
    div.id = 'input-textarea-caret-position-mirror-div';
    document.body.appendChild(div);

    const style = div.style;
    const computed = window.getComputedStyle ? window.getComputedStyle(element) : element.currentStyle;  // currentStyle for IE < 9
    const isInput = element.nodeName === 'INPUT';

    // Default textarea styles
    style.whiteSpace = 'pre-wrap';
    if (!isInput)
        style.wordWrap = 'break-word';  // only for textarea-s

    // Position off-screen
    style.position = 'absolute';  // required to return coordinates properly
    if (!debug)
        style.visibility = 'hidden';  // not 'display: none' because we want rendering

    // Transfer the element's properties to the div
    properties.forEach(function (prop) {
        if (isInput && prop === 'lineHeight') {
            // Special case for <input>s because text is rendered centered and line height may be != height
            if (computed.boxSizing === "border-box") {
                const height = parseInt(computed.height);
                const outerHeight =
                    parseInt(computed.paddingTop) +
                    parseInt(computed.paddingBottom) +
                    parseInt(computed.borderTopWidth) +
                    parseInt(computed.borderBottomWidth);
                const targetHeight = outerHeight + parseInt(computed.lineHeight);
                if (height > targetHeight) {
                    style.lineHeight = height - outerHeight + "px";
                } else if (height === targetHeight) {
                    style.lineHeight = computed.lineHeight;
                } else {
                    style.lineHeight = 0;
                }
            } else {
                style.lineHeight = computed.height;
            }
        } else {
            style[prop] = computed[prop];
        }
    });

    if (isFirefox) {
        // Firefox lies about the overflow property for textareas: https://bugzilla.mozilla.org/show_bug.cgi?id=984275
        if (element.scrollHeight > parseInt(computed.height))
            style.overflowY = 'scroll';
    } else {
        style.overflow = 'hidden';  // for Chrome to not render a scrollbar; IE keeps overflowY = 'scroll'
    }

    div.textContent = element.value.substring(0, position);
    // The second special handling for input type="text" vs textarea:
    // spaces need to be replaced with non-breaking spaces - http://stackoverflow.com/a/13402035/1269037
    if (isInput)
        div.textContent = div.textContent.replace(/\s/g, '\u00a0');

    const span = document.createElement('span');
    // Wrapping must be replicated *exactly*, including when a long word gets
    // onto the next line, with whitespace at the end of the line before (#7).
    // The  *only* reliable way to do that is to copy the *entire* rest of the
    // textarea's content into the <span> created at the caret position.
    // For inputs, just '.' would be enough, but no need to bother.
    span.textContent = element.value.substring(position) || '.';  // || because a completely empty faux span doesn't render at all
    div.appendChild(span);

    const coordinates = {
        top: span.offsetTop + parseInt(computed['borderTopWidth']),
        left: span.offsetLeft + parseInt(computed['borderLeftWidth']),
        height: parseInt(computed['lineHeight'])
    };

    if (debug) {
        span.style.backgroundColor = '#aaa';
    } else {
        document.body.removeChild(div);
    }

    return coordinates;
}

const sleep = (delay) => new Promise((resolve) => setTimeout(resolve, delay));