/**
 * Enhance native <select class="wsdc-select"> into anchored Evolved C dropdowns
 * (.wsdc-dd) — white menu under the trigger, same recipe as site chrome Dashboards.
 * Keeps the original <select> in sync (value + change) so page JS can stay unchanged.
 */
(function (global) {
  "use strict";

  var CHEVRON =
    '<svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">' +
    '<path d="M2.5 4.5L6 8L9.5 4.5" stroke="currentColor" stroke-width="1.5" ' +
    'stroke-linecap="round" stroke-linejoin="round"/></svg>';

  function optionList(select) {
    return Array.prototype.map.call(select.options, function (opt) {
      return {
        value: opt.value,
        label: (opt.textContent || "").trim(),
        disabled: opt.disabled,
        selected: opt.selected,
      };
    });
  }

  function closeAll(except) {
    document.querySelectorAll(".wsdc-dd.is-open").forEach(function (dd) {
      if (except && dd === except) return;
      dd.classList.remove("is-open");
      var btn = dd.querySelector(".wsdc-dd__btn");
      var menu = dd.querySelector(".wsdc-dd__menu");
      if (btn) btn.setAttribute("aria-expanded", "false");
      if (menu) menu.setAttribute("aria-hidden", "true");
    });
  }

  function rebuildMenu(dd, select) {
    var menu = dd.querySelector(".wsdc-dd__menu");
    var valueEl = dd.querySelector(".wsdc-dd__value");
    if (!menu || !valueEl) return;
    menu.innerHTML = "";
    var currentLabel = "";
    optionList(select).forEach(function (opt) {
      var li = document.createElement("li");
      li.setAttribute("role", "none");
      var btn = document.createElement("button");
      btn.type = "button";
      btn.setAttribute("role", "option");
      btn.setAttribute("data-value", opt.value);
      btn.textContent = opt.label;
      if (opt.disabled) btn.disabled = true;
      if (opt.selected) {
        btn.classList.add("is-current");
        btn.setAttribute("aria-selected", "true");
        currentLabel = opt.label;
      } else {
        btn.setAttribute("aria-selected", "false");
      }
      li.appendChild(btn);
      menu.appendChild(li);
    });
    if (!currentLabel && select.options.length) {
      currentLabel = (select.options[select.selectedIndex] || select.options[0]).textContent.trim();
    }
    valueEl.textContent = currentLabel || "";
  }

  function enhance(select) {
    if (!select || select.dataset.wsdcEnhanced === "1") return null;
    select.dataset.wsdcEnhanced = "1";
    select.classList.add("wsdc-select-native");

    var host = document.createElement("div");
    host.className = "wsdc-select-host";

    var dd = document.createElement("div");
    dd.className = "wsdc-dd wsdc-dd--field wsdc-dd--auto";
    dd.style.width = "100%";

    var toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "wsdc-dd__btn";
    toggle.setAttribute("aria-haspopup", "listbox");
    toggle.setAttribute("aria-expanded", "false");
    if (select.id) {
      toggle.id = select.id + "-wsdc-dd-btn";
      var label = document.querySelector('label[for="' + select.id + '"]');
      if (label && !toggle.getAttribute("aria-label")) {
        toggle.setAttribute("aria-labelledby", label.id || "");
        if (!label.id) {
          toggle.setAttribute("aria-label", (label.textContent || "").trim() || select.getAttribute("aria-label") || "Select");
        } else {
          toggle.setAttribute("aria-labelledby", label.id);
        }
      } else if (select.getAttribute("aria-label")) {
        toggle.setAttribute("aria-label", select.getAttribute("aria-label"));
      }
    }

    var valueEl = document.createElement("span");
    valueEl.className = "wsdc-dd__value";
    toggle.appendChild(valueEl);
    toggle.insertAdjacentHTML("beforeend", CHEVRON);

    var menu = document.createElement("ul");
    menu.className = "wsdc-dd__menu";
    menu.setAttribute("role", "listbox");
    menu.setAttribute("aria-hidden", "true");

    dd.appendChild(toggle);
    dd.appendChild(menu);

    var parent = select.parentNode;
    parent.insertBefore(host, select);
    host.appendChild(select);
    host.appendChild(dd);

    rebuildMenu(dd, select);

    toggle.addEventListener("click", function (e) {
      e.preventDefault();
      e.stopPropagation();
      var willOpen = !dd.classList.contains("is-open");
      closeAll();
      if (willOpen) {
        dd.classList.add("is-open");
        toggle.setAttribute("aria-expanded", "true");
        menu.setAttribute("aria-hidden", "false");
      }
    });

    menu.addEventListener("click", function (e) {
      var optBtn = e.target.closest('button[role="option"]');
      if (!optBtn || optBtn.disabled) return;
      e.preventDefault();
      e.stopPropagation();
      var value = optBtn.getAttribute("data-value");
      if (select.value !== value) {
        select.value = value;
        select.dispatchEvent(new Event("change", { bubbles: true }));
      }
      rebuildMenu(dd, select);
      closeAll();
    });

    select.addEventListener("change", function () {
      rebuildMenu(dd, select);
    });

    return dd;
  }

  function refresh(select) {
    if (!select) return;
    if (select.dataset.wsdcEnhanced !== "1") {
      enhance(select);
      return;
    }
    var host = select.closest(".wsdc-select-host");
    var dd = host && host.querySelector(".wsdc-dd");
    if (dd) rebuildMenu(dd, select);
  }

  function enhanceAll(root) {
    var scope = root || document;
    scope.querySelectorAll("select.wsdc-select").forEach(enhance);
  }

  if (!global.__wsdcSelectDocBound) {
    global.__wsdcSelectDocBound = true;
    document.addEventListener("click", function () {
      closeAll();
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") closeAll();
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      enhanceAll();
    });
  } else {
    enhanceAll();
  }

  global.WsdcSelect = {
    enhance: enhance,
    refresh: refresh,
    enhanceAll: enhanceAll,
  };
})(window);
