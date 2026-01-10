"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Plus, BookOpen } from "lucide-react";
import Header from "@/components/Header";
import { useApi } from "@/hooks/useApi";

// const SAMPLE_NOTEBOOKS: Notebook[] = [
//   { id: "1", title: "Biology 101", cardCount: 45, color: "from-emerald-500 to-teal-600" },
//   { id: "2", title: "Spanish Vocabulary", cardCount: 120, color: "from-amber-500 to-orange-600" },
//   { id: "3", title: "History Notes", cardCount: 78, color: "from-sky-500 to-blue-600" },
//   { id: "4", title: "Math Formulas", cardCount: 32, color: "from-violet-500 to-purple-600" },
// ];

export default function Home() {
  const { api, userId, isAuthenticated } = useApi();
  // const [notebooks] = useState<Notebook[]>(SAMPLE_NOTEBOOKS);
  const [notebooks, setNotebooks] = useState<Notebook[]>([]);

  useEffect(() => {
    const fetchNotebooks = async() => {
      try {
        const notebooks = await api.get('/api/notebooks') as Notebook[];
        setNotebooks(notebooks);
      } catch(e) {
        console.error(e);
      }
    }

    if (isAuthenticated) { // TODO: fix this
      fetchNotebooks();
    }
  }, [isAuthenticated])

  const createNotebook = async() => {
    const notebook = await api.post('/api/notebooks', {
      title: "Untitled Notebook"
    });
    // route to new notebook page
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-[#141413]">
      <Header />

      <main className="max-w-6xl mx-auto px-6 py-8">
        <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-6">
          My Notebooks
        </h2>

        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
          {/* Create New Notebook Card */}
          <button onClick={createNotebook} className="aspect-square rounded-xl border-2 border-dashed border-gray-300 dark:border-[#333332] hover:border-amber-400 dark:hover:border-amber-500 hover:bg-gray-100 dark:hover:bg-[#1c1c1b] transition-all flex flex-col items-center justify-center gap-2 group">
            <div className="w-12 h-12 rounded-full bg-gray-200 dark:bg-[#242423] group-hover:bg-amber-100 dark:group-hover:bg-amber-900/30 flex items-center justify-center transition-colors">
              <Plus className="w-6 h-6 text-gray-500 group-hover:text-amber-600 dark:group-hover:text-amber-400 transition-colors" />
            </div>
            <span className="text-sm font-medium text-gray-600 dark:text-gray-400 group-hover:text-amber-600 dark:group-hover:text-amber-400 transition-colors">
              New Notebook
            </span>
          </button>

          {/* Notebook Cards */}
          {notebooks.map((notebook) => (
            <Link
              key={notebook.id}
              href={`/notebook/${notebook.id}`}
              className="aspect-square rounded-xl bg-white dark:bg-[#1c1c1b] shadow-sm hover:shadow-md border border-gray-200 dark:border-[#2a2a29] hover:border-amber-300 dark:hover:border-amber-600/50 transition-all p-4 flex flex-col"
            >
              <div
                className={`w-10 h-10 rounded-lg bg-gradient-to-br ${notebook.color} flex items-center justify-center mb-auto`}
              >
                <BookOpen className="w-5 h-5 text-white" />
              </div>

              <div className="text-left">
                <h3 className="font-medium text-gray-900 dark:text-white text-sm truncate">
                  {notebook.title}
                </h3>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  {notebook.cardCount} cards
                </p>
              </div>
            </Link>
          ))}
        </div>
      </main>
    </div>
  );
}
