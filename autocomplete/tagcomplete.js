let tagCompletionData = {
    ready: false, allTags: [],
    currentCandidates: [], currentIndex: -1, currentRange: null,
};
let popover;
let pendingCompletion;
let suppressNextInput;

// Settings values
let tac_tag_file = "boot_up_dummy.csv";
let tac_active = true
let tac_max_results = 5;
let tac_replace_underscores = true;
let tac_escape_brackets = true;
let tac_append_comma = true;
let tac_append_space = true;
let tac_search_by_alias = true;
let tac_only_show_alias = false;

const WorkingTagDelimiters = ".,/!?%^*;:{}=`~ \n";

const NumberFormatCompact = new Intl.NumberFormat("en", {
    notation: "compact"
});
const NumberFormatSingle = new Intl.NumberFormat("en", {
    notation: "compact",
    minimumFractionDigits: 1,
    maximumFractionDigits: 1
});

function normalize(input) {
    return input.toLowerCase().trim();
}

function hide() {
    popover.hidePopover();
}

function insertSelectedTag(target, tag, selectionStart, selectionEnd) {
    tag = tag.tag.replaceAll("(", "\\(").replaceAll(")", "\\)").replaceAll("_", " ");
    let placed = tag;

    const input = target.value;
    const trailing = input.substring(selectionEnd);

    // Expand placed to include a comma and space if not available
    if (!trailing.trimStart().startsWith(',')) placed = `${placed}, `;

    suppressNextInput = true;

    target.focus();
    target.setSelectionRange(selectionStart, selectionEnd);
    document.execCommand("insertText", false, placed);

    // Gradio callback
    updateInput(target);
}

function performCompletionAndShow(target, caretRect, tag, selectionStart, selectionEnd) {
    tag = tag.replaceAll("\\(", "(").replaceAll("\\)", ")").replaceAll(" ", "_");

    // console.time(`Find candidates: ${tag}`);
    const normalized = normalize(tag);
    const tagword = tag.toLowerCase().replace(/[\n\r]/g, "");
    const candidates = tagCompletionData.currentCandidates = filter_tags_tac(tagCompletionData.allTags, tagword, tac_search_by_alias).slice(0, 5);

    tagCompletionData.currentIndex = -1;
    tagCompletionData.currentRange = {selectionStart, selectionEnd};
    // Guard against empty queries
    if (candidates.length === 0)
        return

    if (candidates[0].tag.length > 1 || (candidates[0].tag.length > 0 && candidates[0].tag !== normalized)) {
        const {left, bottom} = target.getBoundingClientRect();
        const {left: caretLeft} = caretRect;

        popover.style.left = window.scrollX + left + caretLeft + 'px';
        popover.style.top = window.scrollY + bottom + 4 + 'px';

        const ul = popover.querySelector("ul");
        ul.innerHTML = '';
        for (const candidate of candidates) {
            const li = document.createElement("li");
            const label = document.createElement("span");
            // Handle Aliases
            let display_text = "";
            if (candidate.aliases && !candidate.tag.includes(tagword)) {
                let split_aliases = candidate.aliases.split(",");
                let best_alias = split_aliases.find(a => a.toLowerCase().includes(tagword));
                display_text = escapeHTML(best_alias);

                if (!tac_only_show_alias && candidate.tag !== best_alias)
                    display_text += " ➝ " + candidate.tag;
            } else {
                display_text = escapeHTML(candidate.tag);
            }

            label.innerHTML = display_text.replace(tagword, `<b>${tagword}</b>`);
            const count = document.createElement("span");

            // Nicely format the outgoing numbers
            const tag_count = candidate.count;
            let formatter;
            if (tag_count >= 1000000 || (tag_count >= 1000 && tag_count < 10000))
                formatter = NumberFormatSingle;
            else
                formatter = NumberFormatCompact;

            count.textContent = formatter.format(tag_count);
            li.appendChild(label);
            li.appendChild(count);
            li.dataset.class = candidate.category;
            li.addEventListener("click", () => {
                insertSelectedTag(target, candidate, selectionStart, selectionEnd);
                hide();
            });
            ul.appendChild(li);
        }
        popover.scrollTop = 0;
        popover.showPopover();
    } else {
        popover.hidePopover();
    }
    // console.timeEnd(`Find candidates: ${tag}`);
}

function highlightSelectedItem(selectedIndex) {
    tagCompletionData.currentIndex = selectedIndex;

    const ul = popover.querySelector("ul");
    const children = ul.querySelectorAll("li");
    const currentlySelectedItem = ul.querySelector("li[data-selected]");
    if (currentlySelectedItem) delete currentlySelectedItem.dataset.selected;
    if (children[selectedIndex]) children[selectedIndex].dataset.selected = "true";
}

async function initializeData(file) {
    if (file === "not_selected.csv") return;
    if (file === "updating_the.csv") return;
    tagCompletionData.ready = false;
    console.log(`Loading tag completion file ${file}...`);
    console.time('Tag completion file loaded');
    tagCompletionData.allTags = await loadCSV_tac(file);
    console.timeEnd('Tag completion file loaded');
    tagCompletionData.ready = true;
}

function isTargetVisible(target) {
    const {width, height} = target.getBoundingClientRect();
    return width > 0 && height > 0;
}

function initializeDOM() {
    popover = popover = document.createElement("div");
    popover.id = "tagcomplete";
    popover.popover = "manual";
    popover.tabIndex = -1;
    document.body.appendChild(popover);

    const results = document.createElement("ul");
    popover.appendChild(results);
}

async function read_gradio_settings() {
    let tag_file = opts["tac_tagFile"];
    let active = opts["tac_active"];
    let max_results = opts["tac_maxResults"];
    let replace_underscores = opts["tac_replaceUnderscores"];
    let escape_brackets = opts["tac_escapeParentheses"];
    let append_comma = opts["tac_appendComma"];
    let append_space = opts["tac_appendSpace"];
    let search_by_alias = opts["tac_alias.searchByAlias"];
    let only_show_alias = opts["tac_alias.onlyShowAlias"];

    // if only show translation, enable search by translation is necessary
    if (only_show_alias)
        search_by_alias = true;

    if (tag_file !== tac_tag_file) {
        // Reload the Tag CSV on change
        tagCompletionData.allTags = [];
        await initializeData(tag_file);
    }

    tac_tag_file = tag_file;
    tac_active = active;
    tac_max_results = max_results;
    tac_replace_underscores = replace_underscores;
    tac_escape_brackets = escape_brackets;
    tac_append_comma = append_comma;
    tac_append_space = append_space;
    tac_search_by_alias = search_by_alias;
    tac_only_show_alias = only_show_alias;
}

let tac_loading = false;
let tac_loaded_once = false;

async function tac_startup() {
    // Avoid loading multiple times by accident
    if (tac_loading) return;
    // Avoid loading in a state where the opts object has no keys
    if (Object.keys(opts).length === 0) return;
    tac_loading = true;

    // Load and setup data
    if (!tac_loaded_once) {
        initializeDOM();
        tac_loaded_once = true;
    }

    await read_gradio_settings();

    if (pendingCompletion) {
        const {target, caretRect, tag, selectionStart, selectionEnd} = pendingCompletion;
        pendingCompletion = null;
        if (isTargetVisible(target)) performCompletionAndShow(target, caretRect, tag, selectionStart, selectionEnd);
    }
    // Finished loading
    tac_loading = false;
}

onOptionsChanged(async () => {
    await tac_startup();
});

function getWorkingRange(text, selectionStart, selectionEnd) {
    let delimiters = WorkingTagDelimiters;

    // seek backward to find beginning
    while (!delimiters.includes(text[selectionStart - 1]) && selectionStart > 0) {
        selectionStart--;
    }

    // seek forward to find end
    while (!delimiters.includes(text[selectionEnd]) && selectionEnd < text.length) {
        selectionEnd++;
    }

    // // deselect surrounding whitespace
    // while (text[selectionStart] === " " && selectionStart < selectionEnd) {
    //     selectionStart++;
    // }
    // while (text[selectionEnd - 1] === " " && selectionEnd > selectionStart) {
    //     selectionEnd--;
    // }

    // deselect parenthesis
    while (text[selectionStart] === "(" && selectionStart < selectionEnd) {
        selectionStart++;
    }
    while (text[selectionEnd - 1] === ")" && selectionEnd > selectionStart) {
        selectionEnd--;
    }

    return {selectionStart, selectionEnd};
}

function handleInputChange(target) {
    const {selectionStart, selectionEnd} = getWorkingRange(target.value, target.selectionStart, target.selectionEnd);
    const focusTag = target.value.substring(selectionStart, selectionEnd);

    if (!focusTag) {
        hide();
        pendingCompletion = null;
        return;
    }

    const caretRect = getCaretCoordinates(target, selectionEnd);

    if (!tagCompletionData.ready) {
        pendingCompletion = {target, caretRect, tag: focusTag, selectionStart, selectionEnd};
    } else {
        performCompletionAndShow(target, caretRect, focusTag, selectionStart, selectionEnd);
    }
}


// attach event listeners to all matching text elements
const observer = new MutationObserver(() => {
    const textElements = document.querySelectorAll("*:is([id='promptbar'] [id*='_prompt'], .prompt) textarea:not([data-tagcomplete])");
    if (textElements.length === 0) return;

    for (const element of textElements) {
        // handle input changes to text elements
        element.addEventListener("input", (event) => {
            if (!event.inputType && suppressNextInput) return;
            suppressNextInput = false;

            handleInputChange(element);
        });

        // Handle navigation within the autocomplete
        element.addEventListener("keydown", (event) => {
            const currentlyOpen = popover.matches(':popover-open');
            if (event.key === "Escape") {
                if (!currentlyOpen) return;
                event.preventDefault();
                hide();
            } else if (event.key === "ArrowUp") {
                if (!currentlyOpen) return;
                event.preventDefault();
                highlightSelectedItem(tagCompletionData.currentIndex === -1 ?
                    0 :
                    tagCompletionData.currentIndex > 0 ?
                        tagCompletionData.currentIndex - 1 :
                        tagCompletionData.currentCandidates.length - 1);
            } else if (event.key === "ArrowDown") {
                if (!currentlyOpen) return;
                event.preventDefault();
                highlightSelectedItem(tagCompletionData.currentIndex === -1 ?
                    0 :
                    tagCompletionData.currentIndex < tagCompletionData.currentCandidates.length - 1 ?
                        tagCompletionData.currentIndex + 1 :
                        0);
            } else if (event.key === "Tab") {
                if (!currentlyOpen) return;
                event.preventDefault();
                const selectedIndex = tagCompletionData.currentIndex === -1 ? 0 : tagCompletionData.currentIndex;
                const {selectionStart, selectionEnd} = tagCompletionData.currentRange;
                insertSelectedTag(element, tagCompletionData.currentCandidates[selectedIndex], selectionStart, selectionEnd);
                hide();
            } else if (event.key === "Enter") {
                if (!currentlyOpen) return;
                const selectedIndex = tagCompletionData.currentIndex;
                if (selectedIndex === -1) return;
                event.preventDefault();
                const {selectionStart, selectionEnd} = tagCompletionData.currentRange;
                insertSelectedTag(element, tagCompletionData.currentCandidates[selectedIndex], selectionStart, selectionEnd);
                hide();
            }
        });

        // handle focus changes
        element.addEventListener("blur", () => {
            setTimeout(() => {
                const currentlyOpen = popover.matches(':popover-open');
                if (!currentlyOpen || document.activeElement === element || popover.contains(document.activeElement)) return;
                hide();
                pendingCompletion = null;
            });
        });

        element.dataset.tagcomplete = "true";
    }

    observer.disconnect();
});
observer.observe(document, {childList: true, subtree: true});