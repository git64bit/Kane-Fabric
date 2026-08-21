// Kane Fabric v1 Canvas 2D renderer.
//
// This module depends only on the public substrate loader and browser Canvas 2D.
// It has no subscription/application-data input and no third-party JS packages.

import {
  loadSubstrateMetadata,
  openFlatComponent,
  streamLevelChunks,
  SubstrateError,
} from "./kane-fabric-substrate.js";

const DEFAULT_PADDING = 24;

function finiteNumber(value, label) {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    throw new SubstrateError(`${label} must be a finite number`);
  }
  return value;
}

function validateBounds(bounds, label = "bounds") {
  if (!Array.isArray(bounds) || bounds.length !== 4) {
    throw new SubstrateError(`${label} must contain four numbers`);
  }
  const values = bounds.map((value, index) => finiteNumber(value, `${label}[${index}]`));
  if (values[0] >= values[2] || values[1] >= values[3]) {
    throw new SubstrateError(`${label} are empty or invalid`);
  }
  return values;
}

function resolveSubstrateBaseUrl(baseUrl) {
  const text = String(baseUrl);
  const directory = text.endsWith("/") ? text : `${text}/`;
  try {
    return new URL(directory).href;
  } catch (error) {
    const documentUrl = globalThis.location?.href;
    if (!documentUrl) {
      throw new SubstrateError(
        `relative substrate base URL requires a browser document location: ${error.message}`,
      );
    }
    return new URL(directory, documentUrl).href;
  }
}

export function createViewportProjection(bounds, width, height, padding = DEFAULT_PADDING) {
  const [minX, minY, maxX, maxY] = validateBounds(bounds, "viewport bounds");
  finiteNumber(width, "canvas width");
  finiteNumber(height, "canvas height");
  finiteNumber(padding, "canvas padding");
  if (width <= 0 || height <= 0 || padding < 0 || width <= padding * 2 || height <= padding * 2) {
    throw new SubstrateError("canvas dimensions/padding are invalid");
  }

  const spanX = maxX - minX;
  const spanY = maxY - minY;
  const availableWidth = width - padding * 2;
  const availableHeight = height - padding * 2;
  const scale = Math.min(availableWidth / spanX, availableHeight / spanY);
  const drawnWidth = spanX * scale;
  const drawnHeight = spanY * scale;
  const offsetX = (width - drawnWidth) / 2;
  const offsetY = (height - drawnHeight) / 2;

  return {
    bounds: [minX, minY, maxX, maxY],
    height,
    padding,
    scale,
    width,
    project(position) {
      if (!Array.isArray(position) || position.length < 2) {
        throw new SubstrateError("geometry position must contain longitude/latitude");
      }
      const x = finiteNumber(position[0], "longitude");
      const y = finiteNumber(position[1], "latitude");
      return [offsetX + (x - minX) * scale, offsetY + (maxY - y) * scale];
    },
  };
}

function traceLine(ctx, line, projection, close = false) {
  if (!Array.isArray(line) || line.length < 2) {
    throw new SubstrateError("render geometry line is invalid");
  }
  const [firstX, firstY] = projection.project(line[0]);
  ctx.moveTo(firstX, firstY);
  for (let index = 1; index < line.length; index += 1) {
    const [x, y] = projection.project(line[index]);
    ctx.lineTo(x, y);
  }
  if (close) ctx.closePath();
}

function traceGeometry(ctx, geometry, projection) {
  if (!geometry || typeof geometry !== "object" || Array.isArray(geometry)) {
    throw new SubstrateError("render feature geometry is invalid");
  }
  const { type, coordinates } = geometry;
  if (type === "LineString") {
    traceLine(ctx, coordinates, projection);
    return { lineParts: 1, polygonRings: 0 };
  }
  if (type === "MultiLineString") {
    let parts = 0;
    for (const line of coordinates) {
      traceLine(ctx, line, projection);
      parts += 1;
    }
    return { lineParts: parts, polygonRings: 0 };
  }
  if (type === "Polygon") {
    let rings = 0;
    for (const ring of coordinates) {
      traceLine(ctx, ring, projection, true);
      rings += 1;
    }
    return { lineParts: 0, polygonRings: rings };
  }
  if (type === "MultiPolygon") {
    let rings = 0;
    for (const polygon of coordinates) {
      for (const ring of polygon) {
        traceLine(ctx, ring, projection, true);
        rings += 1;
      }
    }
    return { lineParts: 0, polygonRings: rings };
  }
  throw new SubstrateError(`unsupported render geometry type: ${type}`);
}

function drawBoundary(ctx, overview, projection) {
  const rings = overview?.outline?.rings;
  if (!Array.isArray(rings) || rings.length === 0) {
    throw new SubstrateError("county overview has no renderable exterior rings");
  }
  ctx.save();
  ctx.beginPath();
  for (const ring of rings) traceLine(ctx, ring, projection, true);
  ctx.fillStyle = "#f7f7f4";
  ctx.fill("evenodd");
  ctx.strokeStyle = "#444";
  ctx.lineWidth = 1.5;
  ctx.stroke();
  ctx.restore();
  return rings.length;
}

function drawFeature(ctx, feature, projection, role) {
  if (!feature || typeof feature !== "object" || Array.isArray(feature)) {
    throw new SubstrateError(`${role} feature is invalid`);
  }
  ctx.beginPath();
  const traced = traceGeometry(ctx, feature.geometry, projection);

  if (role === "water") {
    if (traced.polygonRings > 0) {
      ctx.fillStyle = "#d9edf7";
      ctx.fill("evenodd");
    }
    ctx.strokeStyle = "#377ea8";
    ctx.lineWidth = 1.2;
    ctx.stroke();
  } else if (role === "roads") {
    ctx.strokeStyle = "#777";
    ctx.lineWidth = 0.8;
    ctx.stroke();
  } else {
    throw new SubstrateError(`unsupported render role: ${role}`);
  }
  return traced;
}

function canvasContext(canvas) {
  if (!canvas || typeof canvas !== "object") {
    throw new SubstrateError("renderer requires a canvas-like object");
  }
  if (!Number.isInteger(canvas.width) || !Number.isInteger(canvas.height) || canvas.width <= 0 || canvas.height <= 0) {
    throw new SubstrateError("renderer canvas width/height are invalid");
  }
  if (typeof canvas.getContext !== "function") {
    throw new SubstrateError("renderer canvas has no getContext method");
  }
  const ctx = canvas.getContext("2d");
  if (!ctx) throw new SubstrateError("Canvas 2D context is unavailable");
  return ctx;
}

export async function renderSubstrate(
  canvas,
  baseUrl,
  {
    bounds = null,
    fetchImpl = fetch,
    padding = DEFAULT_PADDING,
    roadLevel = "orientation",
    runtime = globalThis,
    waterLevel = "overview",
  } = {},
) {
  const ctx = canvasContext(canvas);
  const substrateBaseUrl = resolveSubstrateBaseUrl(baseUrl);
  const metadata = await loadSubstrateMetadata(substrateBaseUrl, { fetchImpl, runtime });
  const fitBounds = validateBounds(metadata.overview.fit.bounds, "overview fit bounds");
  const renderBounds = bounds === null ? fitBounds : validateBounds(bounds, "render bounds");
  const projection = createViewportProjection(renderBounds, canvas.width, canvas.height, padding);

  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = "#fff";
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  const boundaryRingCount = drawBoundary(ctx, metadata.overview, projection);
  const roads = await openFlatComponent(substrateBaseUrl, metadata.manifest, "roads", { fetchImpl, runtime });
  const water = await openFlatComponent(substrateBaseUrl, metadata.manifest, "water", { fetchImpl, runtime });

  const stats = {
    boundary_ring_count: boundaryRingCount,
    jurisdiction: metadata.manifest.jurisdiction,
    roads: { chunk_count: 0, feature_count: 0, line_part_count: 0, polygon_ring_count: 0, level: roadLevel },
    substrate_content_sha256: metadata.manifest.substrate_content_sha256,
    subscription_data_used: false,
    water: { chunk_count: 0, feature_count: 0, line_part_count: 0, polygon_ring_count: 0, level: waterLevel },
  };

  for await (const item of streamLevelChunks(water, waterLevel, { bounds: renderBounds, fetchImpl, runtime })) {
    stats.water.chunk_count += 1;
    stats.water.feature_count += item.features.length;
    for (const feature of item.features) {
      const traced = drawFeature(ctx, feature, projection, "water");
      stats.water.line_part_count += traced.lineParts;
      stats.water.polygon_ring_count += traced.polygonRings;
    }
  }

  for await (const item of streamLevelChunks(roads, roadLevel, { bounds: renderBounds, fetchImpl, runtime })) {
    stats.roads.chunk_count += 1;
    stats.roads.feature_count += item.features.length;
    for (const feature of item.features) {
      const traced = drawFeature(ctx, feature, projection, "roads");
      stats.roads.line_part_count += traced.lineParts;
      stats.roads.polygon_ring_count += traced.polygonRings;
    }
  }

  if (stats.water.feature_count === 0 || stats.roads.feature_count === 0) {
    throw new SubstrateError("selected viewport produced no road or water features");
  }
  return stats;
}
