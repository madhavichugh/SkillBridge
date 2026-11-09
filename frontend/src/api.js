/**
 * Centralized API service for communicating with the SkillBridge backend.
 * Provides easy-to-use async functions with clear error handling.
 */

const API_BASE_URL = 'http://127.0.0.1:8000';

/**
 * Uploads a resume file along with target Job Description text and company profile.
 * Sends data as multipart/form-data.
 */
export async function analyzeResumeAndJD(resumeFile, jdText, companyType = 'mid_size_product') {
  const formData = new FormData();
  if (resumeFile) {
    formData.append('resume_file', resumeFile);
  }
  formData.append('jd_text', jdText);
  formData.append('company_type', companyType);

  const response = await fetch(`${API_BASE_URL}/api/analyze`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Server returned error code ${response.status}`);
  }

  return await response.json();
}

/**
 * Predicts new alignment score when the candidate acquires missing skills.
 */
export async function simulateSkillUplift(simulatePayload) {
  const response = await fetch(`${API_BASE_URL}/api/simulate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(simulatePayload),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Simulation failed with code ${response.status}`);
  }

  return await response.json();
}

/**
 * Generates an effort-vs-impact ranked learning roadmap for missing skills.
 */
export async function getLearningRoadmap(missingSkills, targetRole = 'Software Engineer') {
  const response = await fetch(`${API_BASE_URL}/api/roadmap`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ missing_skills: missingSkills, target_role: targetRole }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Roadmap generation failed`);
  }

  return await response.json();
}

/**
 * Re-frames a project or experience bullet with strong action verbs and [X%] metric placeholders.
 */
export async function rewriteProjectExperience(originalText, targetRole, companyType, targetSkills = []) {
  const response = await fetch(`${API_BASE_URL}/api/rewrite-project`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      original_text: originalText,
      target_role: targetRole,
      company_type: companyType,
      target_skills: targetSkills,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Project re-framing failed`);
  }

  return await response.json();
}

/**
 * Generates 2-3 tailored ATS-ready resume bullets for a specific skill.
 */
export async function generateResumeBullets(skill, roleContext = 'Software Engineer') {
  const response = await fetch(`${API_BASE_URL}/api/generate-bullet`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ skill, role_context: roleContext }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Bullet generation failed`);
  }

  return await response.json();
}

/**
 * Fetches indicative salary ranges and 1-3-5 year growth projections.
 */
export async function getSalaryInsights(role = 'software_engineer', currency = 'USD') {
  const response = await fetch(`${API_BASE_URL}/api/salary?role=${encodeURIComponent(role)}&currency=${encodeURIComponent(currency)}`);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to fetch salary insights`);
  }

  return await response.json();
}

/**
 * Deletes a single user session for privacy compliance.
 */
export async function deleteSession(sessionId) {
  const response = await fetch(`${API_BASE_URL}/api/data/${sessionId}`, {
    method: 'DELETE',
  });
  return response.ok;
}

/**
 * Purges all user data across the system.
 */
export async function purgeAllData() {
  const response = await fetch(`${API_BASE_URL}/api/data`, {
    method: 'DELETE',
  });
  return response.ok;
}
