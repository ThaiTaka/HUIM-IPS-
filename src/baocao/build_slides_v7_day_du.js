// BAOCAO/Slide_HUIM_IPS_V7_day_du.pptx — bộ slide V7 đầy đủ: từ dataset UJIIndoorLoc đến sai số 6,3 m trên tập kiểm tra.
// Không dạy lại lý thuyết HUIM; mỗi slide giải thích ký hiệu, vì sao chọn thuật toán và các con số; ghi chú có kịch bản thuyết trình.
// Số liệu đọc từ BAOCAO/so_lieu_V7/{du_lieu_bao_cao_V7, nguon_goc_hang_so, du_lieu_dataset_uji}.json (không gõ tay).
//
// Chạy (từ thư mục gốc dự án, cần npm "pptxgenjs"; Python có matplotlib, pandas, scikit-learn):
//   python src/baocao/export_why_v7.py ; python src/baocao/export_dataset_v7.py       (sinh hai tệp JSON bằng chứng)
//   node src/baocao/build_slides_v7_day_du.js
const fs = require("fs");
const os = require("os");
const path = require("path");
const { execFileSync } = require("child_process");

const ROOT = path.resolve(__dirname, "..", "..");
const TMP = fs.mkdtempSync(path.join(os.tmpdir(), "slide_v7_dd_"));
const env = { ...process.env, PYTHONIOENCODING: "utf-8" };
execFileSync("python", [path.join(__dirname, "make_slide_v7_assets.py"), TMP], { env });
execFileSync("python", [path.join(__dirname, "make_main_assets_v7.py"), TMP], { env });

const kit = require("./v7_deck_kit.js")({ TMP, ROOT });
require("./dd_part1.js")(kit);
require("./dd_part2.js")(kit);
require("./dd_part3.js")(kit);
require("./dd_part4.js")(kit);

const out = path.join(ROOT, "BAOCAO", "Slide_HUIM_IPS_V7_day_du.pptx");

// pptxgenjs ghi cả ghi chú vào MỘT đoạn văn; tách theo dấu xuống dòng để ghi chú thành các đoạn dễ đọc khi thuyết trình.
async function splitNotes(file) {
  const JSZip = require("jszip");
  const zip = await JSZip.loadAsync(fs.readFileSync(file));
  const re = /<a:p><a:r><a:rPr lang="en-US" dirty="0"\/><a:t>([\s\S]*?)<\/a:t><\/a:r><a:endParaRPr lang="en-US" dirty="0"\/><\/a:p>/;
  let n = 0;
  for (const name of Object.keys(zip.files).filter((f) => /^ppt\/notesSlides\/notesSlide\d+\.xml$/.test(f))) {
    let xml = await zip.file(name).async("string");
    xml = xml.replace(re, (m, body) => {
      n++;
      return body.split(/\r?\n/).map((ln) => `<a:p><a:r><a:rPr lang="vi-VN" dirty="0"/><a:t>${ln}</a:t></a:r></a:p>`).join("");
    });
    zip.file(name, xml);
  }
  fs.writeFileSync(file, await zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }));
  return n;
}

kit.pres.writeFile({ fileName: out }).then(async () => {
  const n = await splitNotes(out);
  fs.rmSync(TMP, { recursive: true, force: true });
  console.log("written", out, fs.statSync(out).size, "slides:", kit.pres.slides.length, "notes tách đoạn:", n);
  kit.warnings.forEach((w) => console.warn("CẢNH BÁO:", w));
});
