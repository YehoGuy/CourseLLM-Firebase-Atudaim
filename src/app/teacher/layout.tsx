

import { FileCode2 } from 'lucide-react'; 
import { AppShell } from '@/components/layout/app-shell';
import {
  BarChart2,
  LayoutDashboard,
  BookOpen,
  Activity 
} from 'lucide-react';
import ClientOnly from '@/components/ClientOnly';
import RoleGuardClient from '@/components/RoleGuardClient';
import InnerAppShellClient from '@/components/InnerAppShellClient';

const teacherNavItems = [
  { href: '/teacher', label: 'Dashboard', icon: <LayoutDashboard /> },
  { href: '/teacher/courses', label: 'Courses', icon: <BookOpen /> },
  { href: '/teacher/material-to-md', label: 'Material to MD', icon: <BarChart2 /> }, // (Assuming you added this from previous steps)
  { href: '/teacher/monitoring', label: 'System Health', icon: <Activity /> }, // <--- Add this line
];

const user = {
  name: 'Dr. Evelyn Reed',
  email: 'e.reed@university.edu',
  avatar: 'https://i.pravatar.cc/150?u=teacher-1',
};




export default function TeacherLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ClientOnly>
      <RoleGuardClient requiredRole="teacher">
        <InnerAppShellClient role="teacher">
          {children}
        </InnerAppShellClient>
      </RoleGuardClient>
    </ClientOnly>
  );
}
