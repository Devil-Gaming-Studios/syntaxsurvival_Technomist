const API_BASE = "http://localhost:8000"; // your FastAPI

function renderForm() {
  const type = document.getElementById("diseaseSelect").value;
  const container = document.getElementById("formContainer");
  container.innerHTML = "";

  if (type === "diabetes") {
    container.innerHTML = `
      <div class="card">
        <h2>Diabetes Input</h2>
        <input id="gender" placeholder="Gender (0/1)">
        <input id="age" placeholder="Age">
        <input id="hypertension" placeholder="Hypertension (0/1)">
        <input id="heart_disease" placeholder="Heart Disease (0/1)">
        <input id="smoking_history" placeholder="Smoking History">
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
        <input id="gender" placeholder="Gender">
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
        <input type="file" id="file">
        <button onclick="submitCovid()">Analyze</button>
      </div>
    `;
  }
}

function showResult(pred, treat) {
  document.getElementById("resultCard").classList.remove("hidden");
  document.getElementById("prediction").innerText = "Prediction: " + pred;
  document.getElementById("treatment").innerText = treat;
}

// ------------------- API CALLS -------------------

async function submitDiabetes() {
  const data = {
    gender: +document.getElementById("gender").value,
    age: +document.getElementById("age").value,
    hypertension: +document.getElementById("hypertension").value,
    heart_disease: +document.getElementById("heart_disease").value,
    smoking_history: +document.getElementById("smoking_history").value,
    bmi: +document.getElementById("bmi").value,
    HbA1c_level: +document.getElementById("hba1c").value,
    blood_glucose_level: +document.getElementById("glucose").value
  };

  const res = await fetch(`${API_BASE}/predict/diabetes`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(data)
  });

  const json = await res.json();
  showResult(json.prediction, json.treatment);
}

async function submitHeart() {
  const data = {
    age: +document.getElementById("age").value,
    gender: +document.getElementById("gender").value,
    cholesterol: +document.getElementById("cholesterol").value,
    rest_bp: +document.getElementById("rest_bp").value,
    max_hr: +document.getElementById("max_hr").value
  };

  const res = await fetch(`${API_BASE}/predict/heart`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(data)
  });

  const json = await res.json();
  showResult(json.prediction, json.treatment);
}

async function submitCovid() {
  const fileInput = document.getElementById("file");
  const formData = new FormData();
  formData.append("file", fileInput.files[0]);

  const res = await fetch(`${API_BASE}/predict/covid`, {
    method: "POST",
    body: formData
  });

  const json = await res.json();
  showResult(json.prediction, json.treatment);
}
