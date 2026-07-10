const chatWindow = document.getElementById("chat-window");
const chatForm = document.getElementById("chat-form");
const queryInput = document.getElementById("query-input");
const sendButton = document.getElementById("send-button");
const formStatus = document.getElementById("form-status");
const metaList = document.getElementById("meta-list");
const userTemplate = document.getElementById("user-message-template");
const assistantTemplate = document.getElementById("assistant-message-template");

const FIELD_LABELS = {
  name_ko: "성명(한글)",
  applicant_name: "신청인 성명(한글)",
  applicant_phone: "신청인 연락처",
  applicant_contact: "신청인 연락처",
  applicant_address: "신청인 주소",
  applicant_birth_date: "신청인 생년월일",
  name_en: "영문 성명",
  first_entry_date: "최초 입국일",
  foreign_address: "해외 거주 주소",
  foreign_email: "해외 이메일",
  foreign_phone: "해외 연락처",
  military_status: "병역 사항",
  stay_purpose: "체류 목적",
  residence_status: "체류 자격",
  emergency_contact_name: "비상연락처 이름",
  emergency_contact_phone: "비상연락처 전화번호",
  emergency_contact_relation: "비상연락처와의 관계",
  resident_registration_number: "주민등록번호",
  applicant_resident_registration_number_or_birth_date: "주민등록번호 또는 생년월일",
  passport_type: "여권 종류",
  passport_pages: "면수",
  passport_period: "유효기간",
  loss_date: "분실 일자",
  loss_place: "분실 장소",
  loss_reason: "분실 사유",
  reporter_name_ko: "신고인 성명(한글)",
  reporter_resident_registration_number: "신고인 주민등록번호",
  reporter_address: "신고인 주소",
  reporter_phone: "신고인 전화번호",
  reporter_mobile_phone: "신고인 휴대전화",
  minor_name: "미성년자 성명(한글)",
  minor_resident_registration_number: "미성년자 주민등록번호",
  minor_address: "미성년자 주소",
  legal_representative_name: "법정대리인 성명(한글)",
  legal_representative_1_name: "법정대리인 1 성명(한글)",
  legal_representative_1_resident_registration_number: "법정대리인 1 주민등록번호",
  legal_representative_1_address: "법정대리인 1 주소",
  legal_representative_1_relationship: "법정대리인과의 관계",
  legal_representative_2_name: "법정대리인 2 성명(한글)",
  legal_representative_2_resident_registration_number: "법정대리인 2 주민등록번호",
  legal_representative_2_address: "법정대리인 2 주소",
  legal_representative_2_relationship: "법정대리인 2와의 관계",
  consent_type: "동의 유형",
  agent_name: "대리인 성명(한글)",
  agent_phone: "대리인 연락처",
  delegation_scope: "위임 범위",
  delegator_name: "위임인 성명(한글)",
  delegator_birth_date: "위임인 생년월일",
  delegator_address: "위임인 주소",
  relationship_to_delegator: "위임인과의 관계",
  relationship_to_applicant: "신청인과의 관계",
  proxy_name: "대리인 성명(한글)",
  proxy_name_ko: "대리인 성명(한글)",
  proxy_contact: "대리인 연락처",
  proxy_resident_registration_number: "대리인 주민등록번호",
  proxy_relationship: "신고인과의 관계",
  passport_number: "여권번호",
  passport_issue_date: "발급일자",
  passport_expiry_date: "기간 만료일",
  passport_expiry_period: "기간 만료일",
  delegation_type: "위임 유형",
  mail_delivery_service: "우편수령 여부",
  confirmation_statement: "확인 문구",
  braille_passport: "점자여권 여부",
  minor_resident_registration_number: "미성년자 주민등록번호",
  minor_address: "미성년자 주소",
  current_passport_number: "현재 여권번호",
  current_passport_issue_date: "현재 여권 발급일",
  current_passport_expiry_date: "현재 여권 만료일",
  current_romanized_name: "현재 로마자 성명",
  new_romanized_name: "변경할 로마자 성명",
  current_english_name: "현재 영문 성명",
  new_english_name: "변경할 영문 성명",
  change_reason_detail: "변경 사유",
  usage_purpose: "사용 목적",
  requested_copy_count: "신청 부수",
  certificate_type: "증명서 종류",
  application_type: "신청 유형",
  mailing_address: "우편 수령 주소",
  writer_name: "작성자 성명",
  writer_phone: "작성자 연락처",
  birth_date: "생년월일",
  address: "주소",
  phone_number: "전화번호",
};

const ROUTE_LABELS = {
  civil_service: "일반 민원",
  emergency_manual: "사건사고 대응",
  needs_clarification: "추가 정보 필요",
};

let conversationContext = null;
let lastRequestPayload = null;
let lastAnswerPayload = null;
let lastDraftPayload = null;
let requestInFlight = false;

async function fetchMeta() {
  try {
    const response = await fetch("/meta");
    if (!response.ok) {
      throw new Error("meta fetch failed");
    }
    const meta = await response.json();
    metaList.innerHTML = `
      <div><dt>청크 수</dt><dd>${meta.chunk_count}</dd></div>
      <div><dt>카테고리</dt><dd>${meta.categories.length}개</dd></div>
      <div><dt>국가</dt><dd>${meta.countries.length}개</dd></div>
      <div><dt>공관</dt><dd>${meta.missions_count}개</dd></div>
    `;
    formStatus.textContent = "백엔드 연결 완료";
  } catch (error) {
    metaList.innerHTML = `<div><dt>상태</dt><dd>연결 실패</dd></div>`;
    formStatus.textContent = "백엔드 연결 실패";
  }
}

function appendUserMessage(text) {
  const fragment = userTemplate.content.cloneNode(true);
  fragment.querySelector(".message-text").textContent = text;
  chatWindow.appendChild(fragment);
  scrollToBottom();
}

function appendAssistantNode(node) {
  const fragment = assistantTemplate.content.cloneNode(true);
  const container = fragment.querySelector(".message-text");
  container.appendChild(node);
  chatWindow.appendChild(fragment);
  scrollToBottom();
}

function appendLoadingMessage() {
  const fragment = assistantTemplate.content.cloneNode(true);
  const message = fragment.querySelector(".message");
  message.classList.add("loading-message");
  fragment.querySelector(".message-text").textContent = "민원 유형을 확인하고 근거 기반 답변을 생성하고 있습니다...";
  chatWindow.appendChild(fragment);
  scrollToBottom();
  return chatWindow.lastElementChild;
}

function setRequestInFlight(isBusy) {
  requestInFlight = isBusy;
  sendButton.disabled = isBusy;
  queryInput.disabled = isBusy;
  document.querySelectorAll(".preset").forEach((button) => {
    button.disabled = isBusy;
  });
}

function scrollToBottom() {
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function createParagraph(text) {
  const paragraph = document.createElement("p");
  paragraph.textContent = text;
  return paragraph;
}

function splitAnswerText(answerText) {
  const sections = [];
  const bullets = [];
  const numberedGroups = [];
  const ignoredPatterns = [/사용자\s*예상\s*질문/i, /사용자\s*예상질문/i];
  let pendingNumber = null;
  let currentNumberGroup = [];
  let currentGroupTitle = null;
  let lastNumberedMax = 0;

  const flushNumberGroup = () => {
    if (!currentNumberGroup.length) {
      return;
    }
    lastNumberedMax = Math.max(...currentNumberGroup.map((item) => item.number));
    numberedGroups.push({
      title: currentGroupTitle,
      items: currentNumberGroup,
    });
    currentNumberGroup = [];
    currentGroupTitle = null;
  };

  const addNumberedItem = (number, text) => {
    const previous = currentNumberGroup[currentNumberGroup.length - 1];
    if (number === 1 && ((previous && previous.number >= 4) || (!previous && lastNumberedMax >= 4))) {
      flushNumberGroup();
      currentGroupTitle = "추가 안내";
      lastNumberedMax = 0;
    }
    currentNumberGroup.push({ number, text });
  };

  const parseNumberedSegments = (line) => {
    const matches = [...line.matchAll(/(\d+)\.\s*/g)];
    if (!matches.length) {
      return null;
    }
    const segments = [];
    for (let index = 0; index < matches.length; index += 1) {
      const match = matches[index];
      const next = matches[index + 1];
      const start = match.index + match[0].length;
      const end = next ? next.index : line.length;
      const text = line.slice(start, end).trim();
      segments.push({ number: Number(match[1]), text });
    }
    return segments;
  };

  const pushSegment = (segment, fromInlineDash = false) => {
    if (!segment) {
      return;
    }
    if (ignoredPatterns.some((pattern) => pattern.test(segment))) {
      return;
    }
    if (/^[-•]\s+/.test(segment)) {
      flushNumberGroup();
      if (pendingNumber) {
        sections.push(pendingNumber);
        pendingNumber = null;
      }
      bullets.push(segment.replace(/^[-•]\s+/, ""));
      return;
    }
    const numberedSegments = parseNumberedSegments(segment);
    if (numberedSegments) {
      if (pendingNumber) {
        addNumberedItem(Number(pendingNumber.replace(".", "")), "");
        pendingNumber = null;
      }
      numberedSegments.forEach(({ number, text }) => {
        if (text) {
          addNumberedItem(number, text);
        } else {
          pendingNumber = `${number}.`;
        }
      });
      return;
    }
    if (pendingNumber) {
      const pendingNumberValue = Number(pendingNumber.replace(".", ""));
      addNumberedItem(pendingNumberValue, segment);
      pendingNumber = null;
      return;
    }
    if (/^(세부\s*안내|세부안내|핵심\s*안내|핵심안내|안내\s*원칙|안내원칙|다음\s*단계|다음단계|추가\s*확인|추가확인|서식\s*안내|서식안내|유의사항|작성\s*지원)[:：]/.test(segment)) {
      flushNumberGroup();
      sections.push(segment);
      return;
    }
    if (fromInlineDash) {
      const cleaned = segment.replace(/^\s+|\s+$/g, "");
      if (cleaned.length <= 28 && !/[.!?。]$/.test(cleaned)) {
        flushNumberGroup();
        sections.push(cleaned);
        return;
      }
      bullets.push(cleaned);
      return;
    }
    const sentences = segment.match(/[^.!?。]+[.!?。]?/g) || [segment];
    sentences
      .map((sentence) => sentence.trim())
      .filter(Boolean)
      .forEach((sentence) => sections.push(sentence));
  };

  String(answerText || "")
    .replaceAll("\r\n", "\n")
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .forEach((line) => {
      const dashedSegments = line
        .split(/\s-\s+/)
        .map((segment) => segment.trim())
        .filter(Boolean);
      if (dashedSegments.length > 1) {
        dashedSegments.forEach((segment, index) => {
          pushSegment(segment, index > 0);
        });
        return;
      }
      pushSegment(line);
    });
  flushNumberGroup();
  if (pendingNumber) {
    sections.push(pendingNumber);
  }
  return { sections, bullets, numberedGroups };
}

function isHeadingLikeBullet(text) {
  const normalized = String(text || "").trim();
  if (!normalized) {
    return false;
  }
  if (/^\d+\.\s*.+$/.test(normalized)) {
    return true;
  }
  if (/[.!?。]$/.test(normalized)) {
    return false;
  }
  if (normalized.length > 18) {
    return false;
  }
  if (/\s{2,}/.test(normalized)) {
    return false;
  }
  return true;
}

function parseLabeledAnswerLine(line) {
  const labelMatch = line.match(/^(세부\s*안내|세부안내|핵심\s*안내|핵심안내|안내\s*원칙|안내원칙|다음\s*단계|다음단계|추가\s*확인|추가확인|서식\s*안내|서식안내|유의사항|작성\s*지원)[:：]\s*(.*)$/);
  if (!labelMatch) {
    return null;
  }
  return {
    label: labelMatch[1].replace(/\s+/g, " "),
    text: labelMatch[2],
  };
}

function createSectionTitle(text) {
  const title = document.createElement("p");
  title.className = "answer-section-title";
  title.textContent = `【${text}】`;
  return title;
}

function createTextBlock(text, className = "") {
  const block = document.createElement("p");
  block.className = className;
  block.textContent = text;
  return block;
}

function createLabeledBlock(label, text) {
  const block = document.createElement("p");
  block.className = "answer-labeled-block";
  const strong = document.createElement("strong");
  strong.textContent = `${label}: `;
  block.appendChild(strong);
  block.appendChild(document.createTextNode(text));
  return block;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function createList(items) {
  const list = document.createElement("ul");
  list.className = "bullet-list";
  items.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    list.appendChild(li);
  });
  return list;
}

function createFieldPromptList(fieldIds, fieldOptionsMap) {
  const list = document.createElement("div");
  list.className = "field-prompt-list";
  fieldIds
    .filter((fieldId, index, array) => array.indexOf(fieldId) === index)
    .forEach((fieldId) => {
      const label = toKoreanFieldLabel(fieldId);
      const options = fieldOptionsMap[fieldId] || [];
      const row = document.createElement("div");
      row.className = "field-prompt-item";

      const heading = document.createElement("div");
      heading.className = "field-prompt-label";
      heading.textContent = label;
      row.appendChild(heading);

      if (options.length) {
        const optionLine = document.createElement("div");
        optionLine.className = "field-prompt-options";
        optionLine.textContent = `선택지: ${options.join(" / ")}`;
        row.appendChild(optionLine);
      }

      list.appendChild(row);
    });
  return list;
}

function createGuidanceBlocks(items) {
  const container = document.createElement("div");
  container.className = "guidance-list";
  items.forEach((item) => {
    if (isHeadingLikeBullet(item)) {
      const heading = document.createElement("p");
      heading.className = "guidance-heading";
      heading.textContent = item;
      container.appendChild(heading);
      return;
    }
    const row = document.createElement("div");
    row.className = "guidance-item";
    const marker = document.createElement("span");
    marker.className = "guidance-marker";
    marker.textContent = "•";
    const text = document.createElement("span");
    text.className = "guidance-text";
    text.textContent = item;
    row.appendChild(marker);
    row.appendChild(text);
    container.appendChild(row);
  });
  return container;
}

function createNumberedGroupBlocks(groups) {
  const container = document.createElement("div");
  container.className = "numbered-groups";
  groups.forEach((group) => {
    if (group.title) {
      const title = document.createElement("p");
      title.className = "numbered-group-title";
      title.textContent = group.title;
      container.appendChild(title);
    }
    group.items.forEach(({ number, text }) => {
      const row = document.createElement("div");
      row.className = "numbered-item";
      const marker = document.createElement("span");
      marker.className = "numbered-marker";
      marker.textContent = `${number}.`;
      const body = document.createElement("span");
      body.className = "numbered-text";
      body.textContent = text;
      row.appendChild(marker);
      row.appendChild(body);
      container.appendChild(row);
    });
  });
  return container;
}

function createChipRow(items) {
  const row = document.createElement("div");
  row.className = "chip-row";
  items.forEach((item) => {
    const chip = document.createElement("span");
    chip.className = "chip";
    chip.textContent = item;
    row.appendChild(chip);
  });
  return row;
}

function toKoreanFieldLabel(fieldId) {
  if (FIELD_LABELS[fieldId]) {
    return FIELD_LABELS[fieldId];
  }
  return `${fieldId.replaceAll("_", " ")} 정보`;
}

function formatOfficeInfo(officeInfo) {
  const labelMap = {
    name: "공관명",
    mission_name: "공관명",
    embassy_name: "공관명",
    country: "국가",
    address: "주소",
    tel: "전화번호",
    phone: "전화번호",
    homepage: "공식 홈페이지",
  };

  const preferredKeys = ["name", "mission_name", "embassy_name", "country", "address", "tel", "phone", "homepage"];
  const lines = [];

  preferredKeys.forEach((key) => {
    if (!(key in officeInfo) || !officeInfo[key]) {
      return;
    }
    const value = officeInfo[key];
    if (typeof value === "object") {
      const homepageValue = value.homepage || value.url || value.link;
      if (homepageValue) {
        lines.push(`공식 홈페이지: ${homepageValue}`);
      }
      return;
    }
    lines.push(`${labelMap[key] ?? key}: ${value}`);
  });

  if (!lines.length) {
    Object.entries(officeInfo).slice(0, 4).forEach(([key, value]) => {
      if (typeof value !== "object" && value) {
        lines.push(`${key}: ${value}`);
      }
    });
  }

  return lines;
}

function createInfoCard(title, bodyLines) {
  const card = document.createElement("article");
  card.className = "info-card";
  const heading = document.createElement("h3");
  heading.textContent = title;
  card.appendChild(heading);
  bodyLines.forEach((line) => {
    card.appendChild(createParagraph(line));
  });
  return card;
}

function buildDraftDocumentHtml(answerPayload, draftPayload, formFilter = null) {
  const classification = answerPayload.classification;
  const forms = (draftPayload.required_forms || []).filter((form) => {
    if (!formFilter) {
      return true;
    }
    return form.form_name === formFilter.form_name || form.form_id === formFilter.form_id;
  });
  const formDraftMap = draftPayload.form_drafts || {};
  const createdAt = new Date().toLocaleString("ko-KR");
  const formsHtml = forms
    .map((form) => {
      const fieldOptions = form.field_options || {};
      const values = formDraftMap[form.form_name] || {};
      const rows = (form.required_fields || [])
        .map((fieldId) => {
          const label = FIELD_LABELS[fieldId] || fieldId;
          const value = values[label] ?? values[fieldId] ?? "";
          const options = fieldOptions[fieldId] || [];
          const normalizedValue = String(value).replace(/\s+/g, "").toLowerCase();
          const optionMarkup = options.length
            ? `
                <div class="option-help">
                  <div class="option-help-label">선택지</div>
                  <div class="option-list">
                    ${options
                      .map((option) => {
                        const normalizedOption = String(option).replace(/\s+/g, "").toLowerCase();
                        const selected =
                          normalizedValue &&
                          (normalizedValue === normalizedOption ||
                            normalizedValue.includes(normalizedOption) ||
                            normalizedOption.includes(normalizedValue));
                        return `
                          <div class="option-item${selected ? " selected" : ""}">
                            <span class="option-checkbox">${selected ? "[v]" : "[]"}</span>
                            <span class="option-text">${escapeHtml(option)}</span>
                          </div>
                        `;
                      })
                      .join("")}
                  </div>
                </div>
              `
            : "";
          const placeholder = value ? escapeHtml(value) : '<span class="field-placeholder">입력 전</span>';
          return `
            <tr>
              <th>${escapeHtml(label)}</th>
              <td>
                <div class="field-value">${placeholder}</div>
                ${optionMarkup}
              </td>
            </tr>
          `;
        })
        .join("");
      return `
        <section class="doc-section">
          <h2>${escapeHtml(form.form_name)}</h2>
          <table>
            <tbody>${rows || `<tr><td colspan="2">입력된 항목이 아직 없습니다.</td></tr>`}</tbody>
          </table>
        </section>
      `;
    })
    .join("");

  return `<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <title>민원서식 초안</title>
  <style>
    body { font-family: "Malgun Gothic", "Segoe UI", sans-serif; background: #f4f1ea; margin: 0; padding: 24px; color: #1f1a17; }
    .page { max-width: 840px; margin: 0 auto; background: #fff; padding: 48px; box-shadow: 0 10px 30px rgba(0,0,0,0.08); }
    h1 { margin: 0 0 8px; font-size: 28px; }
    .meta { color: #5c5147; line-height: 1.7; margin-bottom: 24px; }
    .doc-section { margin-top: 28px; }
    .doc-section h2 { font-size: 20px; margin: 0 0 12px; padding-bottom: 8px; border-bottom: 2px solid #c9b49c; }
    table { width: 100%; border-collapse: collapse; }
    th, td { border: 1px solid #d8cab6; padding: 12px; text-align: left; vertical-align: top; }
    th { width: 32%; background: #f8f3eb; }
    .field-value { min-height: 18px; font-weight: 600; }
    .field-placeholder { color: #9c8f80; }
    .option-help { margin-top: 10px; padding-top: 8px; border-top: 1px dashed #e0d1bd; }
    .option-help-label { font-size: 11px; font-weight: 700; color: #8a4b1e; margin-bottom: 7px; }
    .option-list { display: grid; gap: 4px; }
    .option-item { display: flex; align-items: flex-start; gap: 6px; font-size: 12px; line-height: 1.35; }
    .option-checkbox { flex: 0 0 auto; font-size: 12px; line-height: 1.35; color: #6e4b2f; }
    .option-text { flex: 1 1 auto; min-width: 0; }
    .option-item.selected { font-weight: 700; color: #2f6c5a; }
    .option-item.selected .option-checkbox { color: #2f6c5a; }
    .notice { margin-top: 28px; padding: 16px; background: #fbf7f1; border-left: 4px solid #9b5d31; color: #4d433a; }
    @media print { body { background: #fff; padding: 0; } .page { box-shadow: none; margin: 0; max-width: none; } }
  </style>
</head>
<body>
  <main class="page">
    <h1>재외공관 민원서식 초안</h1>
    <div class="meta">
      <div>민원 분야: ${classification.category ?? "-"}</div>
      <div>국가: ${classification.country ?? "-"}</div>
      <div>관할 공관: ${classification.mission ?? "-"}</div>
      <div>민원명: ${classification.title ?? "-"}</div>
      <div>생성 시각: ${createdAt}</div>
    </div>
    ${formsHtml || "<p>서식 초안 정보가 아직 없습니다.</p>"}
    <div class="notice">
      이 문서는 제출용 원본이 아니라 입력 초안 정리본입니다. 서명, 날짜, 기관 작성란은 현장에서 최종 확인이 필요합니다.
    </div>
  </main>
</body>
</html>`;
}

function sanitizeFilename(value) {
  return String(value || "download")
    .replace(/[\\/:*?"<>|]/g, "_")
    .replace(/\s+/g, "_")
    .slice(0, 80);
}

function createDownloadButton(filename, htmlContent, label = "초안 HTML 다운로드") {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "download-button";
  button.textContent = label;
  button.addEventListener("click", () => {
    const blob = new Blob([htmlContent], { type: "text/html;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
  });
  return button;
}

function printHtmlInPopup(popup, htmlContent) {
  if (!popup) {
    throw new Error("popup blocked");
  }

  popup.document.open();
  popup.document.write(htmlContent);
  popup.document.close();

  const triggerPrint = () => {
    try {
      popup.focus();
      popup.print();
    } catch (error) {
      // Ignore print errors and let the popup stay open.
    }
  };

  if (popup.document.readyState === "complete") {
    setTimeout(triggerPrint, 250);
  } else {
    popup.addEventListener("load", () => setTimeout(triggerPrint, 250), { once: true });
  }
}

function createPdfDownloadButton(payload, label = "초안 PDF 다운로드", filename = "민원서식_초안.pdf", fallbackFilter = null) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "download-button";
  button.textContent = label;
  button.addEventListener("click", async () => {
    button.disabled = true;
    const popup = window.open("", "_blank");
    try {
      const response = await fetch("/export/pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        throw new Error("pdf export failed");
      }
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = filename;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);
      if (popup && !popup.closed) {
        popup.close();
      }
    } catch (error) {
      try {
        if (!lastAnswerPayload || !lastDraftPayload) {
          throw new Error("no cached payload");
        }
        printHtmlInPopup(popup, buildDraftDocumentHtml(lastAnswerPayload, lastDraftPayload, fallbackFilter));
      } catch (fallbackError) {
        alert("PDF 생성에 실패했습니다. HTML 미리보기 인쇄로 대신할 수 없었습니다.");
        if (popup && !popup.closed) {
          popup.close();
        }
      }
    } finally {
      button.disabled = false;
    }
  });
  return button;
}

function createDocumentPreview(answerPayload, draftPayload) {
  const htmlContent = buildDraftDocumentHtml(answerPayload, draftPayload);
  const wrapper = document.createElement("section");
  wrapper.className = "document-preview";

  const header = document.createElement("div");
  header.className = "document-preview-header";
  header.appendChild(createParagraph("문서형 초안 미리보기"));
  const actions = document.createElement("div");
  actions.className = "document-actions";
  actions.appendChild(createDownloadButton("민원서식_초안.html", htmlContent));
  actions.appendChild(
    createPdfDownloadButton(lastRequestPayload || { user_query: "", top_k: 5, context: conversationContext })
  );
  header.appendChild(actions);

  const perFormDownloads = document.createElement("div");
  perFormDownloads.className = "per-form-downloads";
  (draftPayload.required_forms || []).forEach((form) => {
    const formFilter = { form_name: form.form_name, form_id: form.form_id };
    const formHtml = buildDraftDocumentHtml(answerPayload, draftPayload, formFilter);
    const formRow = document.createElement("div");
    formRow.className = "per-form-download";
    const title = document.createElement("span");
    title.className = "per-form-title";
    title.textContent = form.form_name;
    const formActions = document.createElement("div");
    formActions.className = "document-actions";
    const safeName = sanitizeFilename(form.form_name);
    formActions.appendChild(createDownloadButton(`${safeName}.html`, formHtml, "HTML"));
    formActions.appendChild(
      createPdfDownloadButton(
        {
          ...(lastRequestPayload || { user_query: "", top_k: 5, context: conversationContext }),
          form_name: form.form_name,
          form_id: form.form_id,
        },
        "PDF",
        `${safeName}.pdf`,
        formFilter
      )
    );
    formRow.appendChild(title);
    formRow.appendChild(formActions);
    perFormDownloads.appendChild(formRow);
  });

  const frame = document.createElement("iframe");
  frame.className = "document-frame";
  frame.srcdoc = htmlContent;
  frame.title = "민원서식 초안 미리보기";

  wrapper.appendChild(header);
  if (perFormDownloads.children.length) {
    wrapper.appendChild(perFormDownloads);
  }
  wrapper.appendChild(frame);
  return wrapper;
}

function buildAnswerNode(answerPayload, draftPayload) {
  const wrapper = document.createElement("div");
  const classification = answerPayload.classification;
  const hasDraftInputs = Boolean(Object.keys(draftPayload.collected_fields || {}).length);
  const fieldOptionsMap = (draftPayload.required_forms || []).reduce((acc, form) => {
    Object.entries(form.field_options || {}).forEach(([fieldId, options]) => {
      if (!acc[fieldId]) {
        acc[fieldId] = [];
      }
      options.forEach((option) => {
        if (!acc[fieldId].includes(option)) {
          acc[fieldId].push(option);
        }
      });
    });
    return acc;
  }, {});
  const summaryChips = [];
  if (classification.category) {
    summaryChips.push(`민원 분야: ${classification.category}`);
  }
  if (classification.country) {
    summaryChips.push(`국가: ${classification.country}`);
  }
  if (classification.mission) {
    summaryChips.push(`관할 공관: ${classification.mission}`);
  }
  if (classification.route) {
    summaryChips.push(`안내 유형: ${ROUTE_LABELS[classification.route] ?? classification.route}`);
  }
  if (summaryChips.length) {
    wrapper.appendChild(createChipRow(summaryChips));
  }

  const { sections, bullets, numberedGroups } = splitAnswerText(answerPayload.answer);
  if (sections.length) {
    const lead = sections[0];
    wrapper.appendChild(createTextBlock(lead, "answer-lead"));
    const remainder = sections.slice(1);
    remainder.forEach((line) => {
      const labeled = parseLabeledAnswerLine(line);
      if (labeled) {
        wrapper.appendChild(createLabeledBlock(labeled.label, labeled.text));
      } else {
        wrapper.appendChild(createTextBlock(line));
      }
    });
  } else {
    wrapper.appendChild(createTextBlock(answerPayload.answer, "answer-lead"));
  }

  if (!hasDraftInputs) {
    if (bullets.length) {
      wrapper.appendChild(createSectionTitle("핵심 안내"));
      wrapper.appendChild(createGuidanceBlocks(bullets));
    }

    if (numberedGroups.length) {
      wrapper.appendChild(createSectionTitle("절차 안내"));
      wrapper.appendChild(createNumberedGroupBlocks(numberedGroups));
    }

    if (classification.followup_questions?.length) {
      wrapper.appendChild(createSectionTitle("추가 확인"));
      wrapper.appendChild(createList(classification.followup_questions));
    }

    if (answerPayload.suggested_next_steps?.length) {
      wrapper.appendChild(createSectionTitle("다음 단계"));
      wrapper.appendChild(createList(answerPayload.suggested_next_steps));
    }

    const cardGrid = document.createElement("div");
    cardGrid.className = "card-grid";

    if (answerPayload.office_info) {
      const officeLines = formatOfficeInfo(answerPayload.office_info);
      cardGrid.appendChild(createInfoCard("공관 정보", officeLines));
    }

    if (draftPayload.required_forms?.length) {
      const formLines = draftPayload.required_forms.map((form) => {
        const extraDocs = Array.isArray(form.submission_documents) ? form.submission_documents.length : 0;
        const checklist = Array.isArray(form.checklist_items) ? form.checklist_items.length : 0;
        const parts = [];
        if (form.required_fields.length) {
          parts.push(`필수항목 ${form.required_fields.length}개`);
        }
        if (extraDocs) {
          parts.push(`추가 제출서류 ${extraDocs}개`);
        }
        if (checklist) {
          parts.push(`체크리스트 ${checklist}개`);
        }
        return `${form.form_name}${parts.length ? ` / ${parts.join(" / ")}` : ""}`;
      });
      cardGrid.appendChild(createInfoCard("추천 서식", formLines));
    }

    const optionSummaryLines = (draftPayload.required_forms || []).flatMap((form) => {
      const entries = Object.entries(form.field_options || {});
      if (!entries.length) {
        return [];
      }
      const lines = entries.map(([fieldId, options]) => `${toKoreanFieldLabel(fieldId)}: ${options.join(" · ")}`);
      return [`${form.form_name}`, ...lines];
    });
    if (optionSummaryLines.length) {
      cardGrid.appendChild(createInfoCard("선택 예시", optionSummaryLines));
    }

    if (draftPayload.guidance?.length) {
      const conditionGuidance = draftPayload.guidance.filter((line) => line.startsWith("조건 확인:"));
      const generalGuidance = draftPayload.guidance.filter((line) => !line.startsWith("조건 확인:"));
      if (conditionGuidance.length) {
        cardGrid.appendChild(createInfoCard("조건 확인", conditionGuidance.map((line) => line.replace("조건 확인:", "").trim())));
      }
      if (generalGuidance.length) {
        cardGrid.appendChild(createInfoCard("서식 안내", generalGuidance.slice(0, 3)));
      }
    }

    if (answerPayload.safety_notices?.length) {
      const lines = answerPayload.safety_notices.slice(0, 2).map((item) => {
        const values = Object.values(item).slice(0, 3).join(" | ");
        return values;
      });
      cardGrid.appendChild(createInfoCard("안전 공지", lines));
    }

    if (answerPayload.travel_alerts?.length) {
      const lines = answerPayload.travel_alerts.slice(0, 2).map((item) => {
        const values = Object.values(item).slice(0, 3).join(" | ");
        return values;
      });
      cardGrid.appendChild(createInfoCard("여행 경보", lines));
    }

    if (answerPayload.citations?.length) {
      const lines = answerPayload.citations.slice(0, 3).map((citation) => {
        const title = citation.metadata?.title ?? "제목 없음";
        const mission = citation.metadata?.mission ?? citation.metadata?.country ?? "미상";
        return `${title} / ${mission}`;
      });
      cardGrid.appendChild(createInfoCard("근거 문서", lines));
    }

    if (cardGrid.children.length) {
      wrapper.appendChild(cardGrid);
    }

    if (draftPayload.missing_fields?.length) {
      wrapper.appendChild(createSectionTitle("먼저 받아야 할 정보"));
      wrapper.appendChild(
        createFieldPromptList(draftPayload.missing_fields.slice(0, 8), fieldOptionsMap)
      );
    }
  } else {
    if (draftPayload.missing_fields?.length) {
      wrapper.appendChild(createSectionTitle("먼저 받아야 할 정보"));
      wrapper.appendChild(
        createFieldPromptList(draftPayload.missing_fields.slice(0, 8), fieldOptionsMap)
      );
    }
  }

  if (
    (draftPayload.form_drafts && Object.keys(draftPayload.form_drafts).length) ||
    (draftPayload.required_forms && draftPayload.required_forms.some((form) => (form.submission_documents || []).length || (form.checklist_items || []).length))
  ) {
    const draftGrid = document.createElement("div");
    draftGrid.className = "card-grid";
    Object.entries(draftPayload.form_drafts).forEach(([formName, values]) => {
      const lines = Object.entries(values)
        .filter(([, value]) => value !== "" && value !== null && value !== undefined)
        .map(([label, value]) => `${label}: ${value}`);
      if (lines.length) {
        draftGrid.appendChild(createInfoCard(`${formName} 초안`, lines));
      }
    });
    draftPayload.required_forms.forEach((form) => {
      const docLines = [];
      (form.submission_documents || []).slice(0, 6).forEach((item) => {
        if (typeof item === "string") {
          docLines.push(item);
          return;
        }
        if (item?.name) {
          docLines.push(item.condition ? `${item.name} (${item.condition})` : item.name);
        }
      });
      (form.checklist_items || []).slice(0, 6).forEach((item) => docLines.push(item));
      if (docLines.length) {
        draftGrid.appendChild(createInfoCard(`${form.form_name} 추가 서류`, docLines));
      }

    });
    if (draftGrid.children.length) {
      wrapper.appendChild(draftGrid);
      if (draftPayload.form_drafts && Object.keys(draftPayload.form_drafts).length) {
        wrapper.appendChild(createDocumentPreview(answerPayload, draftPayload));
      }
    }
  }

  if (draftPayload.write_support_message) {
    wrapper.appendChild(createSectionTitle("작성 지원"));
    wrapper.appendChild(createTextBlock(draftPayload.write_support_message));
  }

  wrapper.appendChild(createSectionTitle("유의사항"));
  wrapper.appendChild(createTextBlock(answerPayload.disclaimer, "answer-disclaimer"));
  return wrapper;
}

async function askQuestion(query) {
  if (requestInFlight) {
    return;
  }

  appendUserMessage(query);
  setRequestInFlight(true);
  formStatus.textContent = "LLM 답변 생성 중";
  const loadingMessage = appendLoadingMessage();

  try {
    const payload = { user_query: query, top_k: 5, context: conversationContext };
    const response = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error("request failed");
    }

    const responsePayload = await response.json();
    const answerPayload = responsePayload.answer;
    const draftPayload = responsePayload.draft;
    lastAnswerPayload = answerPayload;
    lastDraftPayload = draftPayload;
    conversationContext = {
      route: answerPayload.classification.route,
      category: answerPayload.classification.category,
      country: answerPayload.classification.country,
      mission: answerPayload.classification.mission,
      title: answerPayload.classification.title,
      record_id: answerPayload.classification.record_id,
      draft_template: draftPayload.draft_template,
      required_forms: (draftPayload.required_forms || []).map((form) => form.form_name),
      collected_fields: draftPayload.collected_fields || {},
    };
    lastRequestPayload = { user_query: query, top_k: 5, context: conversationContext };
    appendAssistantNode(buildAnswerNode(answerPayload, draftPayload));
    formStatus.textContent = "응답 완료";
  } catch (error) {
    appendAssistantNode(createParagraph("응답을 불러오지 못했습니다. 백엔드 실행 상태와 API 경로를 확인해 주세요."));
    formStatus.textContent = "응답 실패";
  } finally {
    loadingMessage.remove();
    setRequestInFlight(false);
    queryInput.focus();
  }
}

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const query = queryInput.value.trim();
  if (!query) {
    return;
  }
  queryInput.value = "";
  await askQuestion(query);
});

document.querySelectorAll(".preset").forEach((button) => {
  button.addEventListener("click", async () => {
    const query = button.dataset.query;
    if (query) {
      await askQuestion(query);
    }
  });
});

fetchMeta();
