document.addEventListener("click", async (event) => {
  const addScriptButton = event.target.closest("[data-add-script-segment]");
  if (addScriptButton) {
    addScriptSegment();
    return;
  }

  const removeScriptButton = event.target.closest("[data-remove-script-segment]");
  if (removeScriptButton) {
    removeScriptSegment(removeScriptButton);
    return;
  }

  const copyButton = event.target.closest("[data-copy]");
  if (!copyButton) return;

  try {
    await navigator.clipboard.writeText(copyButton.dataset.copy || "");
    const originalText = copyButton.textContent;
    copyButton.textContent = "Copied";
    setTimeout(() => {
      copyButton.textContent = originalText;
    }, 1200);
  } catch (error) {
    alert("Gagal menyalin teks.");
  }
});

document.addEventListener("submit", (event) => {
  const form = event.target;
  if (form.querySelector("#generator-item-type")) {
    syncGeneratorHiddenFields();
  }
  const message = form.dataset.confirm;
  if (message && !window.confirm(message)) {
    event.preventDefault();
  }
});

const generatorItemOptions = {
  "Batik Fashion": [
    "kemeja batik",
    "blouse batik",
    "dress batik",
    "outer batik",
    "kain batik",
    "custom",
  ],
  "Gadget Product": [
    "iPhone",
    "iPad",
    "MacBook",
    "Apple Watch",
    "AirPods",
    "Android phone",
    "Android tablet",
    "Windows laptop",
    "custom",
  ],
  "Gadget Service": [
    "screen replacement",
    "battery replacement",
    "camera repair",
    "speaker or microphone repair",
    "charging port repair",
    "software troubleshooting",
    "data backup and transfer",
    "cleaning and maintenance",
    "diagnostic check",
    "custom",
  ],
};

function syncGeneratorHiddenFields() {
  const domainSelect = document.querySelector('select[name="product_domain"]');
  const itemSelect = document.querySelector("#generator-item-type");
  const detailInput = document.querySelector("#generator-item-detail");
  if (!domainSelect || !itemSelect) return;

  const domain = domainSelect.value;
  const itemValue = itemSelect.value;
  const detailValue = detailInput ? detailInput.value : "";
  const productType = document.querySelector('input[name="product_type"]');
  const gadgetType = document.querySelector('input[name="gadget_type"]');
  const serviceType = document.querySelector('input[name="service_type"]');
  const customProduct = document.querySelector('input[name="custom_product"]');
  const customGadget = document.querySelector('input[name="custom_gadget"]');
  const customService = document.querySelector('input[name="custom_service"]');

  if (domain === "Batik Fashion") {
    if (productType) productType.value = itemValue;
    if (customProduct) customProduct.value = detailValue;
  } else if (domain === "Gadget Product") {
    if (gadgetType) gadgetType.value = itemValue;
    if (customGadget) customGadget.value = detailValue;
  } else if (domain === "Gadget Service") {
    if (serviceType) serviceType.value = itemValue;
    if (customService) customService.value = detailValue;
  }
}

function updateGeneratorItemType() {
  const domainSelect = document.querySelector('select[name="product_domain"]');
  const itemSelect = document.querySelector("#generator-item-type");
  const detailInput = document.querySelector("#generator-item-detail");
  if (!domainSelect || !itemSelect) return;

  const selectedDomain = domainSelect.value;
  const options = generatorItemOptions[selectedDomain] || generatorItemOptions["Batik Fashion"];
  const previousValue = itemSelect.value || itemSelect.dataset.selected;
  itemSelect.innerHTML = "";

  options.forEach((value) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    option.selected = previousValue === value;
    itemSelect.append(option);
  });

  if (!options.includes(itemSelect.value)) {
    itemSelect.value = options[0];
  }

  if (detailInput) {
    if (selectedDomain === "Batik Fashion") {
      detailInput.placeholder = "example: premium short-sleeve batik shirt, custom motif, cotton fabric";
    } else if (selectedDomain === "Gadget Product") {
      detailInput.placeholder = "example: iPhone 13 Pro 128GB, MacBook Air M1, silver iPad Pro";
    } else {
      detailInput.placeholder = "example: Face ID repair, logic board repair, original-quality battery";
    }
  }

  syncGeneratorHiddenFields();
}

function updateGeneratorDomainFields() {
  const domainSelect = document.querySelector('select[name="product_domain"]');
  if (!domainSelect) return;

  const selectedDomain = domainSelect.value;
  document.querySelectorAll("[data-domain-field]").forEach((field) => {
    const allowedDomains = field.dataset.domainField.split(",");
    const shouldShow = allowedDomains.includes(selectedDomain);
    field.hidden = !shouldShow;
    field.style.display = shouldShow ? "" : "none";
  });
  updateGeneratorItemType();
}

function setGeneratorTalentDefault() {
  const domainSelect = document.querySelector('select[name="product_domain"]');
  const talentSelect = document.querySelector('select[name="model_type"]');
  if (!domainSelect || !talentSelect) return;

  const defaults = {
    "Batik Fashion": "female_influencer",
    "Gadget Product": "tech_reviewer",
    "Gadget Service": "technician",
  };
  talentSelect.value = defaults[domainSelect.value] || "female_influencer";
}

function updateGeneratorScriptFields() {
  const deliverySelect = document.querySelector('select[name="delivery_mode"]');
  const scriptFields = document.querySelector("[data-script-fields]");
  if (!deliverySelect || !scriptFields) return;

  const shouldShow = deliverySelect.value === "talking_script";
  scriptFields.hidden = !shouldShow;
  scriptFields.style.display = shouldShow ? "" : "none";
}

function addScriptSegment() {
  const container = document.querySelector("[data-script-segments]");
  const countInput = document.querySelector("[data-script-segment-count]");
  if (!container || !countInput) return;

  const nextIndex = container.querySelectorAll("[data-script-segment]").length + 1;
  const segment = document.createElement("div");
  segment.className = "script-segment";
  segment.dataset.scriptSegment = "";
  segment.innerHTML = `
    <label data-script-time-label>Time ${nextIndex}
      <input name="script_time_${nextIndex}" placeholder="0:15-0:20">
    </label>
    <label data-script-line-label>Line ${nextIndex}
      <input name="script_line_${nextIndex}" placeholder="Tambahkan kalimat berikutnya...">
    </label>
    <button class="btn btn-small btn-danger script-remove" type="button" data-remove-script-segment>Hapus</button>
  `;
  container.append(segment);
  reindexScriptSegments();
  segment.querySelector("input").focus();
}

function removeScriptSegment(button) {
  const container = document.querySelector("[data-script-segments]");
  const segment = button.closest("[data-script-segment]");
  if (!container || !segment) return;

  const segments = container.querySelectorAll("[data-script-segment]");
  if (segments.length <= 1) {
    segment.querySelectorAll("input").forEach((input) => {
      input.value = "";
    });
    return;
  }

  segment.remove();
  reindexScriptSegments();
}

function reindexScriptSegments() {
  const container = document.querySelector("[data-script-segments]");
  const countInput = document.querySelector("[data-script-segment-count]");
  if (!container || !countInput) return;

  const segments = container.querySelectorAll("[data-script-segment]");
  segments.forEach((segment, index) => {
    const displayIndex = index + 1;
    const timeLabel = segment.querySelector("[data-script-time-label]");
    const lineLabel = segment.querySelector("[data-script-line-label]");
    const timeInput = segment.querySelector('input[name^="script_time_"]');
    const lineInput = segment.querySelector('input[name^="script_line_"]');

    if (timeLabel) timeLabel.firstChild.textContent = `Time ${displayIndex}`;
    if (lineLabel) lineLabel.firstChild.textContent = `Line ${displayIndex}`;
    if (timeInput) timeInput.name = `script_time_${displayIndex}`;
    if (lineInput) lineInput.name = `script_line_${displayIndex}`;
  });
  countInput.value = String(segments.length);
}

document.addEventListener("DOMContentLoaded", () => {
  updateGeneratorDomainFields();
  updateGeneratorScriptFields();
  reindexScriptSegments();
});
document.addEventListener("change", (event) => {
  if (event.target.matches('select[name="product_domain"]')) {
    updateGeneratorDomainFields();
    setGeneratorTalentDefault();
  }
  if (event.target.matches('select[name="delivery_mode"]')) {
    updateGeneratorScriptFields();
  }
  if (event.target.matches("#generator-item-type")) {
    syncGeneratorHiddenFields();
  }
});
document.addEventListener("input", (event) => {
  if (event.target.matches("#generator-item-detail")) {
    syncGeneratorHiddenFields();
  }
});
