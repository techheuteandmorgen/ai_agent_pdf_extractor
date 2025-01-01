import { useState, useEffect } from "react";
import { useRouter } from "next/router";

const Upload = () => {
  const [files, setFiles] = useState([]);
  const [message, setMessage] = useState("");
  const router = useRouter();

  useEffect(() => {
    const isAuthenticated = localStorage.getItem("isAuthenticated");
    if (!isAuthenticated) {
      router.push("/login");
    }
  }, [router]);

  const handleUpload = async () => {
    setMessage("Sending upload request...");
    try {
      const formData = new FormData();
      files.forEach((file) => formData.append("files", file));

      const response = await fetch("http://127.0.0.1:5000/upload", {
        method: "POST",
        body: formData,
        credentials: "include", // Include session cookies
      });

      if (response.ok) {
        const data = await response.json();
        setMessage(data.message || "Upload successful!");
      } else {
        const error = await response.json();
        setMessage(error.message || "Upload failed.");
      }
    } catch (error) {
      setMessage("An error occurred: " + error.message);
    }
  };

  const handleLogout = async () => {
    try {
      const response = await fetch("http://127.0.0.1:5000/logout", {
        method: "POST",
        credentials: "include", // Include session cookies
      });

      if (response.ok) {
        localStorage.removeItem("isAuthenticated");
        router.push("/login");
      }
    } catch (error) {
      setMessage("Logout failed.");
    }
  };

  return (
    <div className="h-screen flex items-center justify-center bg-gray-100">
      <div className="bg-white p-8 shadow-lg rounded-lg">
        <h1 className="text-xl font-bold mb-4">Upload Files</h1>
        <input
          type="file"
          multiple
          onChange={(e) => setFiles(Array.from(e.target.files))}
          className="mb-4"
        />
        <button
          onClick={handleUpload}
          className="bg-blue-500 text-white px-4 py-2 rounded-lg"
        >
          Upload and Process
        </button>
        <button
          onClick={handleLogout}
          className="bg-red-500 text-white px-4 py-2 rounded-lg ml-4"
        >
          Logout
        </button>
        {message && <p className="mt-4 text-red-500">{message}</p>}
      </div>
    </div>
  );
};

export default Upload;