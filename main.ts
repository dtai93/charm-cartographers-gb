import { copyFileSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const source = join(here, "entry.png");
const dest = join(process.env.MAKEFUN_OUTPUT_DIR ?? "/output", "entry.png");

const png = readFileSync(source);
const signature = png.subarray(0, 8).toString("hex");
if (signature !== "89504e470d0a1a0a") {
  throw new Error("entry.png is not a PNG");
}
const width = png.readUInt32BE(16);
const height = png.readUInt32BE(20);
if (width !== 1024 || height !== 1024) {
  throw new Error(`entry.png is ${width}x${height}, expected 1024x1024`);
}
if (png.length > 1_048_576) {
  throw new Error(`entry.png is ${png.length} bytes, over 1048576`);
}

copyFileSync(source, dest);
