import React, { useState, useRef } from 'react';
import { 
  UploadCloud, 
  FileText, 
  Sparkles, 
  AlertCircle,
  FileCheck,
  X
} from 'lucide-react';
import { analyzeResumeAndJD } from '../api';
import LoadingSpinner from '../components/LoadingSpinner';

const SAMPLE_SOFTWARE_JD = `Role: Senior Backend / Full Stack Engineer
Company: CloudScale Technologies

About the Role:
We are looking for a Senior Full Stack Engineer to build high-performance microservices and intuitive web interfaces. You will design, build, and optimize backend APIs, integrate cloud infrastructure, and collaborate with cross-functional product teams.

Requirements & Qualifications:
• 3+ years of professional software engineering experience.
• Strong programming skills in Python (FastAPI/Django) and modern JavaScript/TypeScript.
• Hands-on experience with Relational Databases (PostgreSQL, MySQL) and SQL query optimization.
• Solid background in building and consuming RESTful APIs and Microservices.
• Experience with Docker containerization and CI/CD pipelines (GitHub Actions/Jenkins).
• Familiarity with AWS cloud services (S3, ECS, RDS).
• Knowledge of Redis caching and distributed messaging (Kafka or RabbitMQ) is a strong plus.
• Strong communication, agile collaboration, and problem-solving abilities.
• Bachelor’s degree in Computer Science or equivalent practical industry experience.`;

const SAMPLE_SOFTWARE_RESUME = `Jane Doe
Full Stack Software Developer
Email: jane.doe@example.com | GitHub: github.com/janedoe | LinkedIn: linkedin.com/in/janedoe

Professional Summary:
Software Developer with 3 years of experience developing responsive web applications and backend REST APIs. Proficient in Python, Flask, JavaScript, React, and Git. Passionate about writing clean, maintainable code and collaborating in agile squads.

Technical Skills:
• Languages: Python, JavaScript, HTML5, CSS3, SQL
• Frameworks & Libraries: Flask, React, Node.js, Express, Tailwind CSS
• Databases: PostgreSQL, SQLite
• Tools & Platforms: Git, GitHub, Postman, Linux, VS Code
• Concepts: REST APIs, MVC Architecture, Agile/Scrum, Object-Oriented Programming

Work Experience:
Software Engineer | Apex Digital Solutions (2022 – Present)
• Developed and deployed 12+ RESTful API endpoints using Python Flask and PostgreSQL, reducing query latency by 18%.
• Built dynamic front-end user interfaces using React.js and Tailwind CSS, improving mobile responsiveness.
• Collaborated in bi-weekly Agile sprints, participating in sprint planning and daily standups.
• Created automated unit test suites using PyTest, reaching 85% test coverage across core services.

Junior Web Developer | PixelCraft Studio (2021 – 2022)
• Maintained client web applications built with JavaScript, Node.js, and SQLite.
• Integrated third-party payment gateways and webhook listeners.

Education:
Bachelor of Science in Computer Science | State University (2021)`;

const SAMPLE_ECE_JD = `Role: Embedded Systems / Firmware Engineer
Company: Apex Robotics & Hardware Systems

About the Role:
We are seeking an Embedded Systems Engineer to develop low-level firmware and device drivers for next-generation robotic controllers and IoT sensor platforms. You will work closely with hardware, PCB, and systems teams to bring up new microcontrollers and validate real-time execution.

Requirements & Qualifications:
• 2+ years of hands-on experience in Embedded C / C++ programming for 32-bit microcontrollers (ARM Cortex-M, STM32).
• Strong proficiency in bare-metal programming, FreeRTOS, and peripheral protocols (I2C, SPI, UART, CAN).
• Experience with PCB bring-up, schematic reading, oscilloscope, and logic analyzers.
• Familiarity with Altium Designer or KiCad for hardware debugging and circuit inspection.
• Understanding of Digital Signal Processing (DSP) or control loops (PID) is a strong plus.
• Experience with Git, automated firmware testing, and hardware-in-the-loop (HIL) test benches.
• Bachelor’s degree in Electrical & Electronics Engineering (ECE), Electronics & Communication, or equivalent.`;

const SAMPLE_ECE_RESUME = `Rahul Sharma
Electrical & Electronics Engineer (ECE)
Email: rahul.ece@example.com | GitHub: github.com/rahul-ece | LinkedIn: linkedin.com/in/rahul-ece

Professional Summary:
Electrical and Electronics Engineer with 2.5 years of experience developing embedded firmware, testing microcontrollers, and debugging mixed-signal PCBs. Proficient in Embedded C, STM32, ARM Cortex, I2C, SPI, UART, and Altium Designer. Passionate about IoT edge hardware and reliable firmware architecture.

Technical Skills:
• Programming Languages: Embedded C, C++, Python, MATLAB
• Hardware & Microcontrollers: ARM Cortex-M4, STM32, Arduino, ESP32, 8051
• Protocols & Interfaces: I2C, SPI, UART, GPIO, ADC, PWM
• Tools & EDA Software: Keil uVision, STM32CubeIDE, Altium Designer, KiCad, MATLAB/Simulink
• Laboratory & Testing: Digital Oscilloscope, Logic Analyzer, Multimeter, Soldering, Circuit Debugging
• Concepts: Embedded Systems, Digital Electronics, Analog Circuits, Microprocessors, Sensor Interfacing

Work Experience:
Embedded Hardware Engineer | Cirrus Tech Solutions (2022 – Present)
• Programmed bare-metal firmware routines in Embedded C for STM32F4 microcontrollers, interfacing multi-axis IMU sensors via I2C and SPI.
• Designed and laid out 2-layer sensor breakout PCBs in Altium Designer, reducing signal noise by 15%.
• Conducted benchtop hardware debugging using digital oscilloscopes and logic analyzers to identify bus arbitration faults.
• Integrated UART telemetry streaming to Python-based logging dashboards for environmental test verification.

Graduate Engineer Trainee | ElectroWave Systems (2021 – 2022)
• Assisted senior engineers in schematic capture and BOM component selection for industrial monitoring units.
• Wrote test scripts in Python and C to validate ADC sampling rates and microcontroller power consumption.

Education:
Bachelor of Technology in Electronics and Communication Engineering (ECE) | National Institute of Technology (2021)`;

export default function UploadPage({ onAnalysisComplete }) {
  const [resumeFile, setResumeFile] = useState(null);
  const [jdText, setJdText] = useState('');
  const [companyType, setCompanyType] = useState('mid_size_product');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);
  const fileInputRef = useRef(null);

  // Handle file selection
  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (file.size > 10 * 1024 * 1024) {
        setErrorMessage("File exceeds maximum allowed size of 10 MB.");
        return;
      }
      setResumeFile(file);
      setErrorMessage(null);
    }
  };

  // Quick-load demo data button
  const handleLoadDemo = () => {
    const demoBlob = new Blob([SAMPLE_SOFTWARE_RESUME], { type: 'text/plain' });
    const demoFile = new File([demoBlob], "Jane_Doe_Resume.txt", { type: 'text/plain' });
    setResumeFile(demoFile);
    setJdText(SAMPLE_SOFTWARE_JD);
    setErrorMessage(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!resumeFile) {
      setErrorMessage("Please upload your resume file (PDF, DOCX, or TXT).");
      return;
    }
    if (!jdText.trim() || jdText.trim().length < 30) {
      setErrorMessage("Please paste a complete job description (minimum 30 characters).");
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);

    try {
      const data = await analyzeResumeAndJD(resumeFile, jdText, companyType);
      onAnalysisComplete(data);
    } catch (err) {
      setErrorMessage(err.message || "An unexpected error occurred during analysis.");
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-12">
        <LoadingSpinner message="Evaluating Candidate Alignment with AI & Semantic NLP..." />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Intro Header */}
      <div className="text-center max-w-2xl mx-auto">
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight sm:text-4xl">
          Match Your Resume to Any Target Job
        </h1>
        <p className="mt-3 text-base text-slate-500">
          Upload your resume and paste the target job description. We’ll analyze semantic requirement gaps, qualification alignment, and hiring manager expectations.
        </p>

        {/* Single Demo Button */}
        <div className="mt-4 flex justify-center">
          <button
            type="button"
            onClick={handleLoadDemo}
            className="inline-flex items-center space-x-2 text-xs font-semibold px-3.5 py-1.5 rounded-lg bg-indigo-50 text-indigo-700 hover:bg-indigo-100 transition-colors border border-indigo-200/60 shadow-xs"
          >
            <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
            <span>Load Demo Resume & Job Description</span>
          </button>
        </div>
      </div>

      {errorMessage && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-sm flex items-start space-x-3">
          <AlertCircle className="w-5 h-5 text-rose-600 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <span className="font-semibold">Unable to analyze: </span>
            {errorMessage}
          </div>
          <button onClick={() => setErrorMessage(null)} className="text-rose-500 hover:text-rose-700">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Column: Resume Upload */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-4">
                <label className="block text-sm font-bold text-slate-900">
                  1. Candidate Resume
                </label>
                <span className="text-xs text-slate-400">PDF, DOCX, or TXT</span>
              </div>

              {/* Hidden Native File Input */}
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.docx,.txt"
                onChange={handleFileChange}
                className="hidden"
              />

              {!resumeFile ? (
                <div 
                  onClick={() => fileInputRef.current?.click()}
                  onDragOver={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                  }}
                  onDrop={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                      const file = e.dataTransfer.files[0];
                      if (file.size > 10 * 1024 * 1024) {
                        setErrorMessage("File exceeds maximum allowed size of 10 MB.");
                        return;
                      }
                      setResumeFile(file);
                      setErrorMessage(null);
                    }
                  }}
                  className="border-2 border-dashed border-slate-200 hover:border-indigo-500 hover:bg-indigo-50/20 rounded-2xl p-8 text-center transition-all bg-slate-50/50 flex flex-col items-center justify-center min-h-[260px] cursor-pointer group select-none"
                >
                  <div className="w-14 h-14 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center mb-3 group-hover:scale-105 group-hover:bg-indigo-100 transition-all shadow-xs">
                    <UploadCloud className="w-7 h-7" />
                  </div>
                  <p className="text-sm font-bold text-slate-800 group-hover:text-indigo-600 transition-colors">
                    Click anywhere to upload or drag & drop your resume
                  </p>
                  <p className="text-xs text-slate-400 mt-1.5">
                    Supports PDF, Word (.docx), or plain text (.txt) • Max 10 MB
                  </p>
                  <span className="mt-4 inline-flex items-center text-xs font-semibold px-3 py-1.5 rounded-lg bg-white border border-slate-200 text-slate-600 group-hover:border-indigo-300 group-hover:text-indigo-600 shadow-xs transition-all">
                    Browse Files
                  </span>
                </div>
              ) : (
                <div className="border border-indigo-200 bg-indigo-50/40 rounded-2xl p-6 flex items-center justify-between">
                  <div 
                    onClick={() => fileInputRef.current?.click()}
                    className="flex items-center space-x-3 cursor-pointer flex-1 group"
                    title="Click to choose a different file"
                  >
                    <div className="w-10 h-10 rounded-xl bg-indigo-600 text-white flex items-center justify-center shadow-sm group-hover:bg-indigo-700 transition-colors">
                      <FileCheck className="w-5 h-5" />
                    </div>
                    <div>
                      <p className="text-sm font-bold text-slate-900 truncate max-w-xs group-hover:text-indigo-700 transition-colors">
                        {resumeFile.name}
                      </p>
                      <p className="text-xs text-slate-500">
                        {(resumeFile.size / 1024).toFixed(1)} KB • Ready for NLP parsing • <span className="text-indigo-600 underline">Change</span>
                      </p>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      setResumeFile(null);
                    }}
                    className="p-1.5 text-slate-400 hover:text-rose-600 rounded-lg hover:bg-white transition-colors"
                    title="Remove file"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              )}
            </div>

            <p className="text-[11px] text-slate-400 mt-4">
              🔒 Privacy notice: Your resume is processed in memory and never stored longer than your active session.
            </p>
          </div>

          {/* Right Column: Target Job Description */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="block text-sm font-bold text-slate-900">
                  2. Target Job Description (JD)
                </label>
                <span className="text-xs text-slate-400">{jdText.length} characters</span>
              </div>
              <textarea
                rows={11}
                value={jdText}
                onChange={(e) => setJdText(e.target.value)}
                placeholder="Paste the full job description here, including responsibilities, requirements, and preferred qualifications..."
                className="w-full text-xs font-mono p-3.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 resize-none text-slate-800 placeholder-slate-400"
              />
            </div>
          </div>
        </div>

        {/* Submit Action */}
        <div className="flex justify-center pt-2">
          <button
            type="submit"
            className="inline-flex items-center space-x-2.5 px-8 py-3.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-base shadow-md shadow-indigo-200 hover:shadow-lg transition-all"
          >
            <Sparkles className="w-5 h-5" />
            <span>Analyze Resume Alignment</span>
          </button>
        </div>
      </form>
    </div>
  );
}
