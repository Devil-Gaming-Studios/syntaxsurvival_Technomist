const API_BASE = "https://syntaxsurvival-technomist-2.onrender.com";

// ================================
// FORM RENDERER
// ================================
function renderForm() {
  const type = document.getElementById("diseaseSelect").value;
  const container = document.getElementById("formContainer");
  container.innerHTML = "";

  if (type === "diabetes") {
    container.innerHTML = `
      <div class="card">
        <h2>Diabetes Input</h2>
        <input id="gender" placeholder="Gender (0=Female, 1=Male)">
        <input id="age" placeholder="Age">
        <input id="hypertension" placeholder="Hypertension (0/1)">
        <input id="heart_disease" placeholder="Heart Disease (0/1)">
        <input id="smoking_history" placeholder="Smoking History (0=Never, 1=Former, 2=Current)">
        <input id="bmi" placeholder="BMI">
        <input id="hba1c" placeholder="HbA1c Level">
        <input id="glucose" placeholder="Blood Glucose Level">
        <button onclick="submitDiabetes()">Predict</button>
      </div>
    `;
  }
  else if (type === "heart") {
    container.innerHTML = `
      <div class="card">
        <h2>Heart Disease Input</h2>
        <input id="age" placeholder="Age">
        <input id="gender" placeholder="Gender (0=Female, 1=Male)">
        <input id="cholesterol" placeholder="Cholesterol">
        <input id="rest_bp" placeholder="Resting BP">
        <input id="max_hr" placeholder="Max Heart Rate">
        <button onclick="submitHeart()">Predict</button>
      </div>
    `;
  }
  else if (type === "covid") {
    container.innerHTML = `
      <div class="card">
        <h2>Upload X-ray</h2>
        <input type="file" id="file" accept="image/*">
        <button onclick="submitCovid()">Analyze</button>
      </div>
    `;
  }
}

// ================================
// STREAMING RESULT HANDLER
// ================================
async function streamResult(fetchPromise) {
  document.getElementById("resultCard").classList.remove("hidden");
  document.getElementById("prediction").innerText = "Analysing...";
  document.getElementById("treatment").innerText  = "";

  try {
    const res = await fetchPromise;
    const reader  = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer    = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop();

      for (const line of lines) {
        if (!line.trim()) continue;
        try {
          const data = JSON.parse(line);
          if (data.prediction) {
            document.getElementById("prediction").innerText = "Prediction: " + data.prediction;
          }
          if (data.treatment_chunk) {
            document.getElementById("treatment").innerText += data.treatment_chunk;
          }
        } catch (e) { continue; }
      }
    }

  } catch (e) {
    document.getElementById("prediction").innerText = "Error: " + e.message;
    document.getElementById("treatment").innerText  = "";
  }
}
// ================================
// SUBMIT FUNCTIONS
// ================================
async function submitDiabetes() {
  const data = {
    gender:              +document.getElementById("gender").value,
    age:                 +document.getElementById("age").value,
    hypertension:        +document.getElementById("hypertension").value,
    heart_disease:       +document.getElementById("heart_disease").value,
    smoking_history:     +document.getElementById("smoking_history").value,
    bmi:                 +document.getElementById("bmi").value,
    HbA1c_level:         +document.getElementById("hba1c").value,
    blood_glucose_level: +document.getElementById("glucose").value
  };
  await streamResult(fetch(`${API_BASE}/predict/diabetes`, {
    method:  "POST",
    headers: {"Content-Type": "application/json"},
    body:    JSON.stringify(data)
  }));
}

async function submitHeart() {
  const data = {
    age:         +document.getElementById("age").value,
    gender:      +document.getElementById("gender").value,
    cholesterol: +document.getElementById("cholesterol").value,
    rest_bp:     +document.getElementById("rest_bp").value,
    max_hr:      +document.getElementById("max_hr").value
  };
  await streamResult(fetch(`${API_BASE}/predict/heart`, {
    method:  "POST",
    headers: {"Content-Type": "application/json"},
    body:    JSON.stringify(data)
  }));
}

async function submitCovid() {
  const formData = new FormData();
  formData.append("file", document.getElementById("file").files[0]);
  await streamResult(fetch(`${API_BASE}/predict/covid`, {
    method: "POST",
    body:   formData
  }));
}

// ================================
// HELPERS
// ================================
function setDisease(val) {
  document.getElementById("diseaseSelect").value = val;
  renderForm();
}

function resetResult() {
  document.getElementById("resultCard").classList.add("hidden");
  document.getElementById("prediction").innerText = "";
  document.getElementById("treatment").innerText  = "";
}
