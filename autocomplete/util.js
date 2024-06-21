function parseCSV_tac(str) {
    const arr = [];
    let quote = false;  // 'true' means we're inside a quoted field

    // Iterate over each character, keep track of current row and column (of the returned array)
    for (let row = 0, col = 0, c = 0; c < str.length; c++) {
        let cc = str[c], nc = str[c+1];        // Current character, next character
        arr[row] = arr[row] || [];             // Create a new row if necessary
        arr[row][col] = arr[row][col] || '';   // Create a new column (start with empty string) if necessary

        // If the current character is a quotation mark, and we're inside a
        // quoted field, and the next character is also a quotation mark,
        // add a quotation mark to the current column and skip the next character
        if (cc == '"' && quote && nc == '"') { arr[row][col] += cc; ++c; continue; }

        // If it's just one quotation mark, begin/end quoted field
        if (cc == '"') { quote = !quote; continue; }

        // If it's a comma and we're not in a quoted field, move on to the next column
        if (cc == ',' && !quote) { ++col; continue; }

        // If it's a newline (CRLF), skip the next character and move on to the next row and move to column 0 of that new row
        if (cc == '\r' && nc == '\n') { ++row; col = 0; ++c; quote = false; continue; }

        // If it's a newline (LF or CR) move on to the next row and move to column 0 of that new row
        if (cc == '\n') { ++row; col = 0; quote = false; continue; }
        if (cc == '\r') { ++row; col = 0; quote = false; continue; }

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

    if (response.status != 200) {
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
    results = [];
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

const sleep = (delay) => new Promise((resolve) => setTimeout(resolve, delay))