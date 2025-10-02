import { useState, useEffect} from "react";
import axios from "axios";
import "./App.css";
import FileIcon from "./components/icons/FileIcon";
import UploadIcon from "./components/icons/UploadIcon";
import ImageUploadIcon from "./components/icons/ImageUploadIcon";
import GearIcon from "./components/icons/GearIcon";
import EmailIcon from "./components/icons/EmailIcon";

interface FormData {
  participants: File | null;
  template: File | null;
  emailBody: string;
  x: number | null;
  y: number | null;
  fontsize: number;
  color: string;
  outline: boolean;
  dpi: number;
  senderEmail: string;
  senderPassword: string;
  customSubject: string;
}

interface Status {
  type: "success" | "error" | "loading" | null;
  message: string;
}

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:5000";

function App() {
  const [formData, setFormData] = useState<FormData>({
    participants: null,
    template: null,
    emailBody: "",
    x: null,
    y: null,
    fontsize: 90,
    color: "#000000",
    outline: false,
    dpi: 600,
    senderEmail: "",
    senderPassword: "",
    customSubject: "",
  });

  const [status, setStatus] = useState<Status>({ type: null, message: "" });
  const [isProcessing, setIsProcessing] = useState(false);

  const handleFileChange = (
    field: "participants" | "template",
    file: File | null
  ) => {
    setFormData((prev) => ({ ...prev, [field]: file }));
  };

  const handleInputChange = (field: keyof FormData, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const uploadFiles = async () => {
    if (!formData.participants || !formData.template) {
      setStatus({
        type: "error",
        message:
          "Please select both participants CSV and template image files.",
      });
      return false;
    }

    const uploadFormData = new FormData();
    uploadFormData.append("participants", formData.participants);
    uploadFormData.append("template", formData.template);
    uploadFormData.append("emailBody", formData.emailBody);

    try {
      await axios.post(`${API_BASE}/upload-files`, uploadFormData);
      return true;
    } catch (error) {
      throw new Error("Failed to upload files");
    }
  };

  const generateCertificates = async () => {
    const generateData = {
      x: formData.x,
      y: formData.y,
      fontsize: formData.fontsize,
      color: formData.color,
      outline: formData.outline,
      dpi: formData.dpi,
    };

    try {
      await axios.post(`${API_BASE}/generate-certificates`, generateData);
      return true;
    } catch (error) {
      throw new Error("Failed to generate certificates");
    }
  };

  const sendEmails = async () => {
    if (!formData.senderEmail) {
      throw new Error("Sender email is required");
    }

    const emailData = {
      senderEmail: formData.senderEmail,
      senderPassword: formData.senderPassword,
      customSubject: formData.customSubject,
      dryRun: false,
    };

    try {
      await axios.post(`${API_BASE}/send-emails`, emailData);
      return true;
    } catch (error) {
      throw new Error("Failed to send emails");
    }
  };

  const handleStartProcess = async () => {
    setIsProcessing(true);
    setStatus({ type: "loading", message: "Starting process..." });

    try {
      setStatus({ type: "loading", message: "Uploading files..." });
      await uploadFiles();

      setStatus({ type: "loading", message: "Generating certificates..." });
      await generateCertificates();

      setStatus({ type: "loading", message: "Sending emails..." });
      await sendEmails();

      setStatus({
        type: "success",
        message: "All operations completed successfully!",
      });
    } catch (error) {
      setStatus({
        type: "error",
        message: error instanceof Error ? error.message : "An error occurred",
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const downloadCertificates = async () => {
    try {
      const response = await axios.get(`${API_BASE}/download-certificates`, {
        responseType: "blob",
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "certificates.zip");
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      setStatus({ type: "error", message: "Failed to download certificates" });
    }
  };

  useEffect(() => {
    const checkBackendConnection = async () => {
      try {
        const response = await axios.get(`${API_BASE}/health`);
        console.log("Backend connected:", response.data);
      } catch (error) {
        console.error("Backend connection failed:", error);
      }
    };

    checkBackendConnection();
  }, []);

  return (
    <div className="min-h-screen bg-white">
      <div className="w-full max-w-full px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center mb-12">
          <h1 className="text-4xl lg:text-5xl font-light text-gray-800 mb-4">
            Certificate Generator
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Generate and send personalized certificates effortlessly
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-8 mb-8">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 lg:p-8">
            <div className="flex items-center mb-6">
              <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center mr-3">
                <FileIcon />
              </div>
              <h2 className="text-xl font-medium text-gray-800">
                File Uploads
              </h2>
            </div>

            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Participants CSV File
                </label>
                <div className="relative">
                  <input
                    type="file"
                    accept=".csv"
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                    onChange={(e) =>
                      handleFileChange(
                        "participants",
                        e.target.files?.[0] || null
                      )
                    }
                  />
                  <div
                    className={`
                    flex items-center justify-center p-6 border-2 border-dashed rounded-lg transition-all
                    ${
                      formData.participants
                        ? "border-green-300 bg-green-50 text-green-700"
                        : "border-gray-300 bg-gray-50 text-gray-500 hover:border-blue-300 hover:bg-blue-50"
                    }
                  `}
                  >
                    <div className="text-center">
                      <UploadIcon />
                      <p className="text-sm font-medium">
                        {formData.participants
                          ? formData.participants.name
                          : "Choose CSV file with names and emails"}
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Certificate Template
                </label>
                <div className="relative">
                  <input
                    type="file"
                    accept=".png,.jpg,.jpeg,.svg"
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                    onChange={(e) =>
                      handleFileChange("template", e.target.files?.[0] || null)
                    }
                  />
                  <div
                    className={`
                    flex items-center justify-center p-6 border-2 border-dashed rounded-lg transition-all
                    ${
                      formData.template
                        ? "border-green-300 bg-green-50 text-green-700"
                        : "border-gray-300 bg-gray-50 text-gray-500 hover:border-blue-300 hover:bg-blue-50"
                    }
                  `}
                  >
                    <div className="text-center">
                      <ImageUploadIcon />
                      <p className="text-sm font-medium">
                        {formData.template
                          ? formData.template.name
                          : "Choose template image (PNG, JPG, SVG)"}
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Email Body Template
                </label>
                <textarea
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all resize-none text-sm"
                  placeholder="Enter custom email body (use {name} for recipient name)"
                  rows={4}
                  value={formData.emailBody}
                  onChange={(e) =>
                    handleInputChange("emailBody", e.target.value)
                  }
                />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 lg:p-8">
            <div className="flex items-center mb-6">
              <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center mr-3">
                <GearIcon />
              </div>
              <h2 className="text-xl font-medium text-gray-800">
                Certificate Settings
              </h2>
            </div>

            <div className="grid grid-cols-2 gap-4 mb-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  X Position
                </label>
                <input
                  type="number"
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all text-sm"
                  placeholder="Auto-center"
                  value={formData.x || ""}
                  onChange={(e) =>
                    handleInputChange(
                      "x",
                      e.target.value ? parseInt(e.target.value) : null
                    )
                  }
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Y Position
                </label>
                <input
                  type="number"
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all text-sm"
                  placeholder="Auto-center"
                  value={formData.y || ""}
                  onChange={(e) =>
                    handleInputChange(
                      "y",
                      e.target.value ? parseInt(e.target.value) : null
                    )
                  }
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Font Size
                </label>
                <input
                  type="number"
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all text-sm"
                  value={formData.fontsize}
                  onChange={(e) =>
                    handleInputChange("fontsize", parseInt(e.target.value))
                  }
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Text Color
                </label>
                <input
                  type="color"
                  className="w-full h-11 border border-gray-300 rounded-lg cursor-pointer"
                  value={formData.color}
                  onChange={(e) => handleInputChange("color", e.target.value)}
                />
              </div>

              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  DPI Quality
                </label>
                <input
                  type="number"
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all text-sm"
                  value={formData.dpi}
                  onChange={(e) =>
                    handleInputChange("dpi", parseInt(e.target.value))
                  }
                />
              </div>
            </div>

            <div className="flex items-center space-x-3 p-4 bg-gray-50 rounded-lg">
              <input
                type="checkbox"
                className="w-4 h-4 text-purple-600 rounded focus:ring-purple-500"
                checked={formData.outline}
                onChange={(e) => handleInputChange("outline", e.target.checked)}
              />
              <label className="text-sm font-medium text-gray-700">
                Add text outline for better visibility
              </label>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 lg:p-8 mb-8">
          <div className="flex items-center mb-6">
            <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center mr-3">
              <EmailIcon />
            </div>
            <h2 className="text-xl font-medium text-gray-800">
              Email Configuration
            </h2>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Sender Email
              </label>
              <input
                type="email"
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all text-sm"
                placeholder="your-email@gmail.com"
                value={formData.senderEmail}
                onChange={(e) =>
                  handleInputChange("senderEmail", e.target.value)
                }
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                App Password
              </label>
              <input
                type="password"
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all text-sm"
                placeholder="Gmail app password"
                value={formData.senderPassword}
                onChange={(e) =>
                  handleInputChange("senderPassword", e.target.value)
                }
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Custom Subject (Optional)
              </label>
              <input
                type="text"
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all text-sm"
                placeholder="Your Certificate - {name}"
                value={formData.customSubject}
                onChange={(e) =>
                  handleInputChange("customSubject", e.target.value)
                }
              />
            </div>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row gap-4 justify-center mb-8">
          <button
            className={`
              px-8 py-3 rounded-lg font-medium text-sm transition-all
              ${
                isProcessing ||
                !formData.participants ||
                !formData.template ||
                !formData.senderEmail
                  ? "bg-gray-300 text-gray-500 cursor-not-allowed"
                  : "bg-blue-600 hover:bg-blue-700 text-white shadow-sm hover:shadow-md"
              }
            `}
            onClick={handleStartProcess}
            disabled={
              isProcessing ||
              !formData.participants ||
              !formData.template ||
              !formData.senderEmail
            }
          >
            {isProcessing && <div className="loading-spinner"></div>}
            {isProcessing ? "Processing..." : "Start Generation & Email"}
          </button>

          <button
            className="px-8 py-3 bg-gray-600 hover:bg-gray-700 text-gray-600 font-medium text-sm rounded-lg transition-all shadow-sm hover:shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
            onClick={downloadCertificates}
            disabled={isProcessing}
          >
            Download Certificates
          </button>
        </div>

        {status.type && (
          <div
            className={`
            p-4 rounded-lg text-center font-medium text-sm
            ${
              status.type === "success"
                ? "bg-green-50 text-green-800 border border-green-200"
                : ""
            }
            ${
              status.type === "error"
                ? "bg-red-50 text-red-800 border border-red-200"
                : ""
            }
            ${
              status.type === "loading"
                ? "bg-blue-50 text-blue-800 border border-blue-200"
                : ""
            }
          `}
          >
            <div className="flex items-center justify-center">
              {status.type === "loading" && (
                <div className="loading-spinner"></div>
              )}
              {status.type === "success" && (
                <svg
                  className="w-5 h-5 mr-2"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              )}
              {status.type === "error" && (
                <svg
                  className="w-5 h-5 mr-2"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              )}
              {status.message}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
