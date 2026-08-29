/**
 * Scale a fixed-size Tableau embed into #vizViewport without collapsing to scale(0)
 * when layout is not ready yet (common after chrome inject / background tabs).
 */
(function (global) {
  function readSize(el) {
    if (!el) return { w: 0, h: 0 };
    return { w: el.clientWidth || 0, h: el.clientHeight || 0 };
  }

  function applyScale(viewport, scaled, vizW, vizH) {
    var size = readSize(viewport);
    if (size.w < 2 || size.h < 2) return false;
    var scale = Math.min(size.w / vizW, size.h / vizH, 1);
    if (!(scale > 0)) return false;
    scaled.style.transform = "scale(" + scale + ")";
    return true;
  }

  /**
   * @param {{ width: number, height: number, viewportId?: string, scaledId?: string }} opts
   */
  global.wsdcBindFitViz = function wsdcBindFitViz(opts) {
    var vizW = opts && opts.width;
    var vizH = opts && opts.height;
    var viewportId = (opts && opts.viewportId) || "vizViewport";
    var scaledId = (opts && opts.scaledId) || "vizScaled";
    if (!(vizW > 0) || !(vizH > 0)) return;

    var tries = 0;
    var maxTries = 180;

    function fit() {
      var viewport = document.getElementById(viewportId);
      var scaled = document.getElementById(scaledId);
      if (!viewport || !scaled) return;
      if (applyScale(viewport, scaled, vizW, vizH)) return;
      if (tries < maxTries) {
        tries += 1;
        global.requestAnimationFrame(fit);
      }
    }

    fit();
    global.addEventListener("resize", fit);
    global.addEventListener("load", fit);

    var viewport = document.getElementById(viewportId);
    if (viewport && typeof ResizeObserver !== "undefined") {
      new ResizeObserver(fit).observe(viewport);
    }
  };
})(window);
