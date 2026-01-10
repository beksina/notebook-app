"use client";

import { useState } from "react";
import { useSession, signOut } from "next-auth/react";
import { Settings, LogOut } from "lucide-react";
import Image from "next/image";

export default function Header() {
  const { data: session } = useSession();
  const [showDropdown, setShowDropdown] = useState(false);

  const userInitial = session?.user?.name?.[0]?.toUpperCase() || "U";

  return (
    <header className="flex items-center justify-between px-6 py-4 bg-white dark:bg-[#1c1c1b] border-b border-gray-200 dark:border-[#2a2a29]">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
        RecallPro
      </h1>

      <div className="flex items-center gap-4">
        <button
          className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-[#242423] transition-colors"
          aria-label="Settings"
        >
          <Settings className="w-5 h-5 text-gray-600 dark:text-gray-400" />
        </button>

        <div className="relative">
          <button
            onClick={() => setShowDropdown(!showDropdown)}
            className="w-9 h-9 rounded-full bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center text-white font-medium text-sm overflow-hidden"
            aria-label="User profile"
          >
            {session?.user?.image ? (
              <Image
                src={session.user.image}
                alt={session.user.name || "User"}
                width={36}
                height={36}
                className="w-full h-full object-cover"
              />
            ) : (
              userInitial
            )}
          </button>

          {showDropdown && (
            <>
              <div
                className="fixed inset-0 z-10"
                onClick={() => setShowDropdown(false)}
              />
              <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-[#1c1c1b] rounded-lg shadow-lg border border-gray-200 dark:border-[#2a2a29] py-1 z-20">
                <div className="px-4 py-2 border-b border-gray-200 dark:border-[#2a2a29]">
                  <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                    {session?.user?.name}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                    {session?.user?.email}
                  </p>
                </div>
                <button
                  onClick={() => signOut({ callbackUrl: "/login" })}
                  className="w-full flex items-center gap-2 px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-[#242423]"
                >
                  <LogOut className="w-4 h-4" />
                  Sign out
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
