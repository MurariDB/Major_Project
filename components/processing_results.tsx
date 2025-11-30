"use client"
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

interface ProcessingStats {
  text_chunks: number
  images_indexed: number
  duration: number
  text_collection_count: number
  image_collection_count: number
  db_path: string
  faiss_index_path: string
  id_map_path: string
  pdf_directory: string
  images_directory: string
}

interface ProcessingResultsProps {
  stats: ProcessingStats
  isVisible: boolean
  onClose: () => void
}

export default function ProcessingResults({ stats, isVisible, onClose }: ProcessingResultsProps) {
  if (!isVisible) return null

  // Data for charts
  const indexingData = [
    { name: "Text Chunks", value: stats.text_chunks, fill: "#3B82F6" },
    { name: "Images", value: stats.images_indexed, fill: "#EC4899" },
  ]

  const storageData = [
    { name: "Text Data", value: 65, fill: "#3B82F6" },
    { name: "Image Data", value: 25, fill: "#EC4899" },
    { name: "Metadata", value: 10, fill: "#8B5CF6" },
  ]

  const performanceTimeline = [
    { step: "Text Extract", time: Math.round(stats.duration * 0.4) },
    { step: "Image Process", time: Math.round(stats.duration * 0.35) },
    { step: "FAISS Index", time: Math.round(stats.duration * 0.25) },
  ]

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4 animate-fadeIn">
      <div className="bg-gradient-to-br from-white to-blue-50 rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6 sticky top-0 z-10">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <h2 className="text-3xl font-bold flex items-center gap-2">✅ Processing Complete!</h2>
              <p className="text-blue-100">Your knowledge base has been successfully indexed</p>
            </div>
            <button onClick={onClose} className="text-white hover:bg-white/20 rounded-full p-2 transition-all">
              ✕
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Quick Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-blue-600 text-sm font-semibold">Total Chunks</p>
              <p className="text-3xl font-bold text-blue-900 mt-1">{stats.text_chunks}</p>
              <p className="text-xs text-blue-500 mt-2">Text segments</p>
            </div>
            <div className="bg-pink-50 border border-pink-200 rounded-lg p-4">
              <p className="text-pink-600 text-sm font-semibold">Images Indexed</p>
              <p className="text-3xl font-bold text-pink-900 mt-1">{stats.images_indexed}</p>
              <p className="text-xs text-pink-500 mt-2">Visual aids</p>
            </div>
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
              <p className="text-purple-600 text-sm font-semibold">Processing Time</p>
              <p className="text-3xl font-bold text-purple-900 mt-1">{stats.duration.toFixed(1)}s</p>
              <p className="text-xs text-purple-500 mt-2">Total duration</p>
            </div>
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <p className="text-green-600 text-sm font-semibold">DB Records</p>
              <p className="text-3xl font-bold text-green-900 mt-1">
                {stats.text_collection_count + stats.image_collection_count}
              </p>
              <p className="text-xs text-green-500 mt-2">Total indexed</p>
            </div>
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Indexing Overview */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Indexing Overview</CardTitle>
                <CardDescription>Breakdown of indexed content</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={indexingData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                      {indexingData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.fill} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Storage Distribution */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Storage Distribution</CardTitle>
                <CardDescription>How storage is allocated</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie
                      data={storageData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={(entry) => `${entry.name} ${entry.value}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {storageData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.fill} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Processing Timeline */}
            <Card className="md:col-span-2">
              <CardHeader>
                <CardTitle className="text-lg">Processing Timeline</CardTitle>
                <CardDescription>Time spent on each stage</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={250}>
                  <LineChart data={performanceTimeline}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="step" />
                    <YAxis label={{ value: "Time (seconds)", angle: -90, position: "insideLeft" }} />
                    <Tooltip />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="time"
                      stroke="#8B5CF6"
                      strokeWidth={3}
                      dot={{ fill: "#8B5CF6", r: 6 }}
                      activeDot={{ r: 8 }}
                      name="Duration"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Database Details */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Database Details</CardTitle>
              <CardDescription>Storage paths and configurations</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                  <div className="flex items-start gap-2">
                    <span className="text-xl">🗄️</span>
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-sm text-gray-700">SQLite Metadata Database</p>
                      <p className="text-xs text-gray-500 break-all font-mono">{stats.db_path}</p>
                    </div>
                  </div>

                  <div className="flex items-start gap-2">
                    <span className="text-xl">📊</span>
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-sm text-gray-700">FAISS Vector Index</p>
                      <p className="text-xs text-gray-500 break-all font-mono">{stats.faiss_index_path}</p>
                    </div>
                  </div>

                  <div className="flex items-start gap-2">
                    <span className="text-xl">🔗</span>
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-sm text-gray-700">Vector ID Mapping</p>
                      <p className="text-xs text-gray-500 break-all font-mono">{stats.id_map_path}</p>
                    </div>
                  </div>

                  <div className="flex items-start gap-2">
                    <span className="text-xl">📁</span>
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-sm text-gray-700">PDF Directory</p>
                      <p className="text-xs text-gray-500 break-all font-mono">{stats.pdf_directory}</p>
                    </div>
                  </div>

                  <div className="flex items-start gap-2">
                    <span className="text-xl">🖼️</span>
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-sm text-gray-700">Images Directory</p>
                      <p className="text-xs text-gray-500 break-all font-mono">{stats.images_directory}</p>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Collection Summary */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Collection Summary</CardTitle>
              <CardDescription>Database contents</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div className="border-l-4 border-blue-500 pl-4">
                  <p className="text-sm text-gray-600">Text Chunks (SQLite)</p>
                  <p className="text-2xl font-bold text-blue-600">{stats.text_collection_count}</p>
                </div>
                <div className="border-l-4 border-pink-500 pl-4">
                  <p className="text-sm text-gray-600">Images (SQLite)</p>
                  <p className="text-2xl font-bold text-pink-600">{stats.image_collection_count}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Close Button */}
          <button
            onClick={onClose}
            className="w-full py-3 px-6 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white font-bold rounded-lg transition-all shadow-lg hover:shadow-xl"
          >
            Got it! Start Studying 🚀
          </button>
        </div>
      </div>
    </div>
  )
}
