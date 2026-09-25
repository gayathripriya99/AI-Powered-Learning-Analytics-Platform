// DocumentUpload.tsx
// This component lets users upload PDF/DOCX/TXT files
// Think of it like a file drop zone connected to our backend

import { useState } from 'react'

// TypeScript: define what a Document looks like
interface Document {
  id: number
  filename: string
  created_at: string
}

function DocumentUpload() {
  const [documents, setDocuments] = useState<Document[]>([])  // list of uploaded docs
  const [uploading, setUploading] = useState(false)           // is file uploading?
  const [message, setMessage] = useState('')                  // success/error message

  const API_URL = import.meta.env.VITE_API_URL ||
    (typeof window !== 'undefined' && window.location.hostname.includes('vercel.app')
      ? 'https://ai-powered-learning-analytics-platform.onrender.com'
      : 'http://127.0.0.1:8000')

  // This runs when user picks a file
  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setUploading(true)
    setMessage('')

    // FormData is how we send files to the server
    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch(`${API_URL}/documents/upload`, {
        method: 'POST',
        body: formData  // no Content-Type header needed for files!
      })
      const data = await response.json()

      if (data.error) {
        setMessage(`❌ Error: ${data.error}`)
      } else {
        setMessage(`✅ Uploaded! ${data.filename} (${data.characters} characters)`)
        fetchDocuments()  // refresh the list
      }
    } catch (error) {
      setMessage('❌ Could not connect to server')
    }

    setUploading(false)
  }

  // Fetch all uploaded documents
  const fetchDocuments = async () => {
    try {
      const response = await fetch(`${API_URL}/documents`)
      const data = await response.json()
      setDocuments(data.documents || [])
    } catch (error) {
      console.error('Could not fetch documents')
    }
  }

  // Load documents when component first shows
  useState(() => {
    fetchDocuments()
  })

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      
      {/* Header */}
      <div className="max-w-3xl mx-auto">
        <h1 className="text-2xl font-bold text-purple-400 mb-2">📄 Document Center</h1>
        <p className="text-gray-400 mb-6">Upload PDFs, Word docs, or text files to ask questions about them</p>

        {/* Upload Box */}
        <div className="bg-gray-800 border-2 border-dashed border-gray-600 rounded-xl p-8 text-center mb-6">
          <p className="text-4xl mb-3">📁</p>
          <p className="text-gray-300 mb-4">Choose a file to upload</p>
          <p className="text-gray-500 text-sm mb-4">Supports: PDF, DOCX, TXT</p>
          
          {/* Hidden file input - styled button triggers it */}
          <label className="cursor-pointer bg-purple-600 hover:bg-purple-700 px-6 py-3 rounded-lg font-bold">
            {uploading ? 'Uploading...' : 'Choose File'}
            <input
              type="file"
              accept=".pdf,.docx,.txt"
              onChange={handleUpload}
              className="hidden"  // hide the ugly default input
              disabled={uploading}
            />
          </label>
        </div>

        {/* Success/Error message */}
        {message && (
          <div className={`p-3 rounded-lg mb-6 ${message.includes('✅') ? 'bg-green-800' : 'bg-red-800'}`}>
            {message}
          </div>
        )}

        {/* List of uploaded documents */}
        <h2 className="text-lg font-bold text-gray-300 mb-3">📚 Uploaded Documents</h2>
        {documents.length === 0 ? (
          <p className="text-gray-500">No documents uploaded yet.</p>
        ) : (
          <div className="space-y-2">
            {documents.map(doc => (
              <div key={doc.id} className="bg-gray-800 p-3 rounded-lg flex justify-between items-center">
                <span className="text-gray-200">📄 {doc.filename}</span>
                <span className="text-gray-500 text-sm">{new Date(doc.created_at).toLocaleDateString()}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default DocumentUpload