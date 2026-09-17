export class AdministrativeDescriptorError extends Error {
  constructor(message, path = "descriptor") {
    super(`${path}: ${message}`);
    this.name = "AdministrativeDescriptorError";
    this.path = path;
  }
}

const CONTROL_KINDS = new Set([
  "text",
  "number",
  "date",
  "select",
  "textarea",
  "checkbox",
  "notice",
  "collection",
]);

const INPUT_KINDS = new Set(["text", "number", "date", "select", "textarea", "checkbox"]);

function isObject(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function requireObject(value, path) {
  if (!isObject(value)) throw new AdministrativeDescriptorError("must be an object", path);
  return value;
}

function requireArray(value, path, { nonEmpty = false } = {}) {
  if (!Array.isArray(value)) throw new AdministrativeDescriptorError("must be an array", path);
  if (nonEmpty && value.length === 0) throw new AdministrativeDescriptorError("must not be empty", path);
  return value;
}

function requireString(value, path) {
  if (typeof value !== "string" || value.trim() === "") {
    throw new AdministrativeDescriptorError("must be a non-empty string", path);
  }
  return value;
}

function requirePositiveInteger(value, path) {
  if (!Number.isInteger(value) || value < 1) {
    throw new AdministrativeDescriptorError("must be a positive integer", path);
  }
  return value;
}

function validateLayout(layout, path, columns) {
  if (layout === undefined) return;
  requireObject(layout, path);
  if (layout.row !== undefined) requirePositiveInteger(layout.row, `${path}.row`);
  if (layout.column !== undefined) requirePositiveInteger(layout.column, `${path}.column`);
  if (layout.span !== undefined) requirePositiveInteger(layout.span, `${path}.span`);
  if (layout.column !== undefined && layout.column > columns) {
    throw new AdministrativeDescriptorError(`column exceeds section grid width ${columns}`, `${path}.column`);
  }
  if (layout.span !== undefined && layout.span > columns) {
    throw new AdministrativeDescriptorError(`span exceeds section grid width ${columns}`, `${path}.span`);
  }
}

function validateAuthorityRefs(refs, path, authorityIds) {
  if (refs === undefined) return;
  requireArray(refs, path);
  refs.forEach((ref, index) => {
    requireString(ref, `${path}[${index}]`);
    if (!authorityIds.has(ref)) {
      throw new AdministrativeDescriptorError(`unknown authority reference ${ref}`, `${path}[${index}]`);
    }
  });
}

function validateControl(control, path, context) {
  requireObject(control, path);
  requireString(control.id, `${path}.id`);
  requireString(control.kind, `${path}.kind`);
  if (!CONTROL_KINDS.has(control.kind)) {
    throw new AdministrativeDescriptorError(`unsupported control kind ${control.kind}`, `${path}.kind`);
  }
  if (context.controlIds.has(control.id)) {
    throw new AdministrativeDescriptorError(`duplicate control id ${control.id}`, `${path}.id`);
  }
  context.controlIds.add(control.id);

  if (control.kind !== "notice") requireString(control.label, `${path}.label`);
  if (INPUT_KINDS.has(control.kind) || control.kind === "collection") {
    requireString(control.binding, `${path}.binding`);
  }
  if (control.unit !== undefined) requireString(control.unit, `${path}.unit`);
  if (control.format !== undefined) requireString(control.format, `${path}.format`);
  validateLayout(control.layout, `${path}.layout`, context.columns);
  validateAuthorityRefs(control.authority_refs, `${path}.authority_refs`, context.authorityIds);

  if (control.visible_when !== undefined) {
    requireObject(control.visible_when, `${path}.visible_when`);
    requireString(control.visible_when.binding, `${path}.visible_when.binding`);
    if (!("equals" in control.visible_when)) {
      throw new AdministrativeDescriptorError("must declare equals", `${path}.visible_when`);
    }
  }

  if (control.kind === "select") {
    requireArray(control.options, `${path}.options`, { nonEmpty: true });
    control.options.forEach((option, index) => {
      requireObject(option, `${path}.options[${index}]`);
      requireString(option.value, `${path}.options[${index}].value`);
      requireString(option.label, `${path}.options[${index}].label`);
    });
  }

  if (control.kind === "notice") requireString(control.text, `${path}.text`);

  if (control.kind === "collection") {
    requireArray(control.item_controls, `${path}.item_controls`, { nonEmpty: true });
    const itemColumns = control.item_layout?.columns ?? context.columns;
    requirePositiveInteger(itemColumns, `${path}.item_layout.columns`);
    const nestedContext = { ...context, columns: itemColumns };
    control.item_controls.forEach((itemControl, index) => {
      validateControl(itemControl, `${path}.item_controls[${index}]`, nestedContext);
    });
  }
}

export function validateAdministrativeDescriptor(descriptor) {
  requireObject(descriptor, "descriptor");
  if (descriptor.format !== "kane-fabric-administrative-descriptor") {
    throw new AdministrativeDescriptorError("unsupported format", "descriptor.format");
  }
  if (descriptor.format_version !== 1) {
    throw new AdministrativeDescriptorError("unsupported format version", "descriptor.format_version");
  }
  requireString(descriptor.descriptor_id, "descriptor.descriptor_id");
  requirePositiveInteger(descriptor.descriptor_version, "descriptor.descriptor_version");
  requireString(descriptor.title, "descriptor.title");
  requireObject(descriptor.scope, "descriptor.scope");

  if (descriptor.categories !== undefined) {
    const categories = requireArray(descriptor.categories, "descriptor.categories");
    const categoryIds = new Set();
    categories.forEach((category, index) => {
      const path = `descriptor.categories[${index}]`;
      requireObject(category, path);
      requireString(category.id, `${path}.id`);
      requireString(category.label, `${path}.label`);
      if (categoryIds.has(category.id)) {
        throw new AdministrativeDescriptorError(`duplicate category id ${category.id}`, `${path}.id`);
      }
      categoryIds.add(category.id);
    });
  }

  const authorities = requireArray(descriptor.authorities ?? [], "descriptor.authorities");
  const authorityIds = new Set();
  authorities.forEach((authority, index) => {
    const path = `descriptor.authorities[${index}]`;
    requireObject(authority, path);
    requireString(authority.id, `${path}.id`);
    requireString(authority.kind, `${path}.kind`);
    requireString(authority.citation, `${path}.citation`);
    if (authorityIds.has(authority.id)) {
      throw new AdministrativeDescriptorError(`duplicate authority id ${authority.id}`, `${path}.id`);
    }
    authorityIds.add(authority.id);
  });

  const pages = requireArray(descriptor.pages, "descriptor.pages", { nonEmpty: true });
  const pageIds = new Set();
  const sectionIds = new Set();
  const controlIds = new Set();
  pages.forEach((page, pageIndex) => {
    const pagePath = `descriptor.pages[${pageIndex}]`;
    requireObject(page, pagePath);
    requireString(page.id, `${pagePath}.id`);
    requireString(page.title, `${pagePath}.title`);
    if (pageIds.has(page.id)) throw new AdministrativeDescriptorError(`duplicate page id ${page.id}`, `${pagePath}.id`);
    pageIds.add(page.id);

    const sections = requireArray(page.sections, `${pagePath}.sections`, { nonEmpty: true });
    sections.forEach((section, sectionIndex) => {
      const sectionPath = `${pagePath}.sections[${sectionIndex}]`;
      requireObject(section, sectionPath);
      requireString(section.id, `${sectionPath}.id`);
      requireString(section.title, `${sectionPath}.title`);
      if (sectionIds.has(section.id)) {
        throw new AdministrativeDescriptorError(`duplicate section id ${section.id}`, `${sectionPath}.id`);
      }
      sectionIds.add(section.id);
      const columns = section.layout?.columns ?? 12;
      requirePositiveInteger(columns, `${sectionPath}.layout.columns`);
      validateAuthorityRefs(section.authority_refs, `${sectionPath}.authority_refs`, authorityIds);
      const controls = requireArray(section.controls, `${sectionPath}.controls`, { nonEmpty: true });
      const context = { columns, authorityIds, controlIds };
      controls.forEach((control, controlIndex) => {
        validateControl(control, `${sectionPath}.controls[${controlIndex}]`, context);
      });
    });
  });

  return descriptor;
}

export function canonicalizeJson(value) {
  if (Array.isArray(value)) return `[${value.map((entry) => canonicalizeJson(entry)).join(",")}]`;
  if (isObject(value)) {
    return `{${Object.keys(value)
      .sort()
      .map((key) => `${JSON.stringify(key)}:${canonicalizeJson(value[key])}`)
      .join(",")}}`;
  }
  return JSON.stringify(value);
}

export async function sha256CanonicalJson(value) {
  const bytes = new TextEncoder().encode(canonicalizeJson(value));
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("");
}

export function descriptorSummary(descriptor) {
  validateAdministrativeDescriptor(descriptor);
  let sections = 0;
  let controls = 0;
  let collections = 0;
  descriptor.pages.forEach((page) => {
    sections += page.sections.length;
    page.sections.forEach((section) => {
      const countControls = (items) => {
        items.forEach((control) => {
          controls += 1;
          if (control.kind === "collection") {
            collections += 1;
            countControls(control.item_controls);
          }
        });
      };
      countControls(section.controls);
    });
  });
  return {
    descriptor_id: descriptor.descriptor_id,
    descriptor_version: descriptor.descriptor_version,
    pages: descriptor.pages.length,
    sections,
    controls,
    collections,
  };
}

function cloneJson(value) {
  return value === undefined ? undefined : JSON.parse(JSON.stringify(value));
}

function splitBinding(binding) {
  return binding.split(".").filter(Boolean);
}

function getPath(root, binding) {
  let cursor = root;
  for (const key of splitBinding(binding)) {
    if (cursor === null || cursor === undefined) return undefined;
    cursor = cursor[key];
  }
  return cursor;
}

function setPath(root, binding, value) {
  const parts = splitBinding(binding);
  let cursor = root;
  parts.forEach((part, index) => {
    const last = index === parts.length - 1;
    if (last) {
      cursor[part] = value;
      return;
    }
    const nextPart = parts[index + 1];
    const nextIsIndex = /^\d+$/.test(nextPart);
    if (cursor[part] === undefined || cursor[part] === null) cursor[part] = nextIsIndex ? [] : {};
    cursor = cursor[part];
  });
}

function fieldId(prefix, binding) {
  return `${prefix}-${binding.replace(/[^a-zA-Z0-9_-]+/g, "-")}`;
}

function applyLayout(element, layout = {}) {
  if (layout.column !== undefined || layout.span !== undefined) {
    const column = layout.column ?? "auto";
    const span = layout.span ?? 1;
    element.style.gridColumn = `${column} / span ${span}`;
  }
  if (layout.row !== undefined) element.style.gridRow = String(layout.row);
}

function renderAuthorityLinks(container, refs, authorityMap) {
  if (!refs?.length) return;
  const list = document.createElement("div");
  list.className = "admin-authority-links";
  refs.forEach((ref) => {
    const authority = authorityMap.get(ref);
    const item = authority?.url ? document.createElement("a") : document.createElement("span");
    item.textContent = authority?.citation ?? ref;
    if (authority?.url) {
      item.href = authority.url;
      item.target = "_blank";
      item.rel = "noreferrer";
    }
    list.append(item);
  });
  container.append(list);
}

function renderHelp(container, control) {
  if (!control.help) return;
  const help = document.createElement("p");
  help.className = "admin-help";
  help.textContent = control.help;
  container.append(help);
}

function createInput(control, binding, state, onStateChange, prefix) {
  let input;
  if (control.kind === "textarea") {
    input = document.createElement("textarea");
    if (control.rows) input.rows = control.rows;
    if (control.cols) input.cols = control.cols;
  } else if (control.kind === "select") {
    input = document.createElement("select");
    control.options.forEach((option) => {
      const node = document.createElement("option");
      node.value = option.value;
      node.textContent = option.label;
      input.append(node);
    });
  } else {
    input = document.createElement("input");
    input.type = control.kind === "checkbox" ? "checkbox" : control.kind;
  }

  input.id = fieldId(prefix, binding);
  input.name = binding;
  input.required = control.required === true;
  input.disabled = control.disabled === true;
  input.readOnly = control.readonly === true;
  if (control.placeholder !== undefined) input.placeholder = control.placeholder;
  if (control.min !== undefined) input.min = String(control.min);
  if (control.max !== undefined) input.max = String(control.max);
  if (control.step !== undefined) input.step = String(control.step);

  const existing = getPath(state, binding);
  if (control.kind === "checkbox") input.checked = existing === true;
  else if (existing !== undefined && existing !== null) input.value = String(existing);
  else if (control.default !== undefined) {
    if (control.kind === "checkbox") input.checked = control.default === true;
    else input.value = String(control.default);
    setPath(state, binding, control.default);
  }

  const eventName = control.kind === "select" || control.kind === "checkbox" ? "change" : "input";
  input.addEventListener(eventName, () => {
    let value;
    if (control.kind === "checkbox") value = input.checked;
    else if (control.kind === "number") value = input.value === "" ? null : Number(input.value);
    else value = input.value;
    setPath(state, binding, value);
    onStateChange();
  });
  return input;
}

function visibleFor(control, state) {
  if (!control.visible_when) return true;
  return getPath(state, control.visible_when.binding) === control.visible_when.equals;
}

export function renderAdministrativeDescriptor(container, descriptor, options = {}) {
  validateAdministrativeDescriptor(descriptor);
  const state = cloneJson(options.initialData ?? {}) ?? {};
  const authorityMap = new Map(descriptor.authorities.map((authority) => [authority.id, authority]));
  const conditionalNodes = [];
  const prefix = options.idPrefix ?? descriptor.descriptor_id.replace(/[^a-zA-Z0-9_-]+/g, "-");

  container.replaceChildren();
  container.classList.add("admin-descriptor");

  const header = document.createElement("header");
  header.className = "admin-descriptor-header";
  const eyebrow = document.createElement("p");
  eyebrow.className = "admin-kicker";
  eyebrow.textContent = descriptor.scope.label ?? descriptor.scope.state_code ?? "Civic Infrastructure";
  const title = document.createElement("h2");
  title.textContent = descriptor.title;
  header.append(eyebrow, title);
  if (descriptor.help) {
    const help = document.createElement("p");
    help.className = "admin-descriptor-help";
    help.textContent = descriptor.help;
    header.append(help);
  }
  container.append(header);

  const reevaluateVisibility = () => {
    conditionalNodes.forEach(({ node, control }) => {
      node.hidden = !visibleFor(control, state);
    });
  };

  const renderControl = (control, target, bindingPrefix = "", localColumns = 12) => {
    const binding = control.binding
      ? [bindingPrefix, control.binding].filter(Boolean).join(".")
      : null;
    const wrapper = document.createElement(control.kind === "collection" ? "fieldset" : "div");
    wrapper.className = `admin-control admin-control-${control.kind}`;
    wrapper.dataset.controlId = control.id;
    if (control.data_role) wrapper.dataset.dataRole = control.data_role;
    applyLayout(wrapper, control.layout);
    if (control.visible_when) conditionalNodes.push({ node: wrapper, control: {
      ...control,
      visible_when: {
        ...control.visible_when,
        binding: [bindingPrefix, control.visible_when.binding].filter(Boolean).join("."),
      },
    } });

    if (control.kind === "notice") {
      const text = document.createElement("p");
      text.className = "admin-notice-text";
      text.textContent = control.text;
      wrapper.append(text);
      renderAuthorityLinks(wrapper, control.authority_refs, authorityMap);
      target.append(wrapper);
      return;
    }

    if (control.kind === "collection") {
      const legend = document.createElement("legend");
      legend.textContent = control.label;
      wrapper.append(legend);
      renderHelp(wrapper, control);
      renderAuthorityLinks(wrapper, control.authority_refs, authorityMap);
      const items = document.createElement("div");
      items.className = "admin-collection-items";
      wrapper.append(items);
      target.append(wrapper);

      let values = getPath(state, binding);
      if (!Array.isArray(values)) {
        values = [];
        setPath(state, binding, values);
      }
      const minimum = control.min_items ?? 0;
      while (values.length < minimum) values.push({});

      const renderItems = () => {
        items.replaceChildren();
        values.forEach((_, index) => {
          const item = document.createElement("div");
          item.className = "admin-collection-item";
          item.style.setProperty("--admin-columns", String(control.item_layout?.columns ?? localColumns));
          const itemHeader = document.createElement("div");
          itemHeader.className = "admin-collection-item-header";
          const itemTitle = document.createElement("strong");
          itemTitle.textContent = `${control.item_label ?? "Item"} ${index + 1}`;
          const remove = document.createElement("button");
          remove.type = "button";
          remove.textContent = control.actions?.remove_label ?? "Remove";
          remove.disabled = values.length <= minimum;
          remove.addEventListener("click", () => {
            values.splice(index, 1);
            renderItems();
            reevaluateVisibility();
          });
          itemHeader.append(itemTitle, remove);
          item.append(itemHeader);
          control.item_controls.forEach((itemControl) => {
            renderControl(itemControl, item, `${binding}.${index}`, control.item_layout?.columns ?? localColumns);
          });
          items.append(item);
        });
      };

      renderItems();
      const add = document.createElement("button");
      add.type = "button";
      add.className = "admin-add-item";
      add.textContent = control.actions?.add_label ?? `Add ${control.item_label ?? "item"}`;
      add.addEventListener("click", () => {
        values.push({});
        renderItems();
        reevaluateVisibility();
      });
      wrapper.append(add);
      return;
    }

    const label = document.createElement("label");
    label.htmlFor = fieldId(prefix, binding);
    label.textContent = control.label;
    wrapper.append(label);
    const input = createInput(control, binding, state, reevaluateVisibility, prefix);
    wrapper.append(input);
    renderHelp(wrapper, control);
    renderAuthorityLinks(wrapper, control.authority_refs, authorityMap);
    target.append(wrapper);
  };

  descriptor.pages.forEach((page) => {
    const pageNode = document.createElement("article");
    pageNode.className = "admin-page";
    pageNode.dataset.pageId = page.id;
    const pageTitle = document.createElement("h3");
    pageTitle.textContent = page.title;
    pageNode.append(pageTitle);
    if (page.help) {
      const pageHelp = document.createElement("p");
      pageHelp.className = "admin-page-help";
      pageHelp.textContent = page.help;
      pageNode.append(pageHelp);
    }

    page.sections.forEach((section) => {
      const sectionNode = document.createElement("section");
      sectionNode.className = "admin-section";
      sectionNode.dataset.sectionId = section.id;
      const sectionTitle = document.createElement("h4");
      sectionTitle.textContent = section.title;
      sectionNode.append(sectionTitle);
      if (section.help) {
        const sectionHelp = document.createElement("p");
        sectionHelp.className = "admin-section-help";
        sectionHelp.textContent = section.help;
        sectionNode.append(sectionHelp);
      }
      renderAuthorityLinks(sectionNode, section.authority_refs, authorityMap);
      const grid = document.createElement("div");
      grid.className = "admin-grid";
      grid.style.setProperty("--admin-columns", String(section.layout?.columns ?? 12));
      section.controls.forEach((control) => renderControl(control, grid, "", section.layout?.columns ?? 12));
      sectionNode.append(grid);
      pageNode.append(sectionNode);
    });
    container.append(pageNode);
  });

  reevaluateVisibility();
  return {
    descriptor,
    getData: () => cloneJson(state),
  };
}
