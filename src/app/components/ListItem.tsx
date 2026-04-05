import { useState } from "react";
import { useNavigate } from "react-router";
import { Upload, X } from "lucide-react";
import { ImageWithFallback } from "./figma/ImageWithFallback";
import { authFetch } from "../auth";

type UploadResponse = {
  upload_url: string;
  file_url: string;
  method: "PUT";
  headers: Record<string, string>;
};

export function ListItem() {
  const navigate = useNavigate();
  const [itemName, setItemName] = useState("");
  const [condition, setCondition] = useState<"Good" | "Fair" | "Poor">("Good");
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedImage(file);
      const reader = new FileReader();
      reader.onload = () => setImagePreview(reader.result as string);
      reader.readAsDataURL(file);
    }
  };

  const resetSelectedImage = () => {
    setSelectedImage(null);
    setImagePreview(null);
  };

  const uploadImage = async (file: File): Promise<string> => {
    const presignResponse = await authFetch("/uploads/presign", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        file_name: file.name,
        content_type: file.type,
        folder: "items",
      }),
    });

    if (!presignResponse.ok) {
      console.error("Presign response failed:", await presignResponse.text());
      throw new Error("Failed to prepare image upload");
    }

    const uploadData: UploadResponse = await presignResponse.json();
    console.log("Presigned upload URL and data:", uploadData);

    const uploadResponse = await fetch(uploadData.upload_url, {
      method: uploadData.method,
      headers: uploadData.headers,
      body: file,
    });

    if (!uploadResponse.ok) {
      console.error("S3 Upload failed:", uploadResponse.status, await uploadResponse.text());
      throw new Error(`Failed to upload image directly to S3 (status ${uploadResponse.status})`);
    }

    console.log("S3 Upload successful! File available at:", uploadData.file_url);
    return uploadData.file_url;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const ownerId = localStorage.getItem("guest_user_id");
    if (!ownerId) {
      setError("Please select an account on the Profile page first.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const imageUrls = selectedImage ? [await uploadImage(selectedImage)] : [];
      const res = await authFetch("/items/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          owner_id: ownerId,
          name: itemName,
          category: "other",
          condition: condition.toLowerCase(),
          price: 1, // Placeholder — pricing agent updates in background
          confidence_score: null,
          image_urls: imageUrls,
        }),
      });
      if (!res.ok) throw new Error("Failed to list item");
      navigate("/my-items");
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-[1100px] mx-auto px-8 py-8">
      <div className="max-w-[600px] mx-auto">
        <h1 className="mb-8" style={{ fontSize: '32px', fontWeight: 600, color: '#1A1A1A' }}>
          List an Item
        </h1>

        <form onSubmit={handleSubmit} className="bg-white rounded-xl p-8 space-y-6">
          {/* Photo Upload */}
          <div>
            <label className="block mb-3" style={{ fontSize: '16px', fontWeight: 600, color: '#1A1A1A' }}>
              Photo
            </label>
            {!imagePreview ? (
              <label className="flex flex-col items-center justify-center w-full h-64 border-2 border-dashed border-[#E5E5E5] rounded-xl cursor-pointer hover:border-[#534AB7] transition-colors bg-[#F9F9F9]">
                <Upload className="w-12 h-12 text-[#6B6B6B] mb-3" />
                <span className="text-[#6B6B6B]">Drag and drop or click to upload</span>
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleImageUpload}
                  className="hidden"
                />
              </label>
            ) : (
              <div className="relative">
                <ImageWithFallback
                  src={imagePreview}
                  alt="Preview"
                  className="w-full h-64 object-cover rounded-xl"
                />
                <button
                  type="button"
                  onClick={resetSelectedImage}
                  className="absolute top-3 right-3 w-10 h-10 bg-white rounded-full flex items-center justify-center shadow-lg hover:bg-gray-100 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            )}
          </div>

          {/* Item Name */}
          <div>
            <label className="block mb-3" style={{ fontSize: '16px', fontWeight: 600, color: '#1A1A1A' }}>
              Item Name
            </label>
            <input
              type="text"
              value={itemName}
              onChange={(e) => setItemName(e.target.value)}
              placeholder="e.g., Calculus Textbook"
              required
              className="w-full px-4 py-3 border border-[#E5E5E5] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#534AB7]"
            />
          </div>

          {/* Condition */}
          <div>
            <label className="block mb-3" style={{ fontSize: '16px', fontWeight: 600, color: '#1A1A1A' }}>
              Condition
            </label>
            <div className="flex gap-3">
              {(["Good", "Fair", "Poor"] as const).map((cond) => (
                <button
                  key={cond}
                  type="button"
                  onClick={() => setCondition(cond)}
                  className={`flex-1 py-3 rounded-lg transition-colors ${
                    condition === cond
                      ? "bg-[#534AB7] text-white"
                      : "bg-[#F3F4F6] text-[#1A1A1A] hover:bg-[#E5E5E5]"
                  }`}
                >
                  {cond}
                </button>
              ))}
            </div>
          </div>

          {/* Helper Text */}
          <p className="text-[#6B6B6B] text-sm">
            We will upload your image to S3 first, then create the item using the returned image URL.
          </p>

          {/* Error Message */}
          {error && <div className="text-red-500">{error}</div>}

          {/* Submit Button */}
          <button
            type="submit"
            className="w-full py-4 bg-[#534AB7] text-white rounded-lg hover:bg-[#453CA0] transition-colors"
            style={{ fontSize: '18px', fontWeight: 600 }}
            disabled={loading}
          >
            {loading ? "Listing..." : "List Item"}
          </button>
        </form>
      </div>
    </div>
  );
}
