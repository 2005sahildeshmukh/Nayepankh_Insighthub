import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, Settings, Activity, Wand2, BarChart2 } from 'lucide-react';

interface DatasetTabsProps {
  workspaceId: string;
  datasetId: string;
}

export function DatasetTabs({ workspaceId, datasetId }: DatasetTabsProps) {
  const pathname = usePathname();
  const basePath = `/w/${workspaceId}/datasets/${datasetId}`;

  const tabs = [
    {
      name: 'Overview',
      href: basePath,
      icon: LayoutDashboard,
      exact: true,
    },
    {
      name: 'Mapping',
      href: `${basePath}/mapping`,
      icon: Settings,
      exact: false,
    },
    {
      name: 'Profile & Quality',
      href: `${basePath}/profile`,
      icon: Activity,
      exact: false,
    },
    {
      name: 'Cleaning',
      href: `${basePath}/cleaning`,
      icon: Wand2,
      exact: false,
    },
    {
      name: 'Analytics',
      href: `${basePath}/analytics`,
      icon: BarChart2,
      exact: false,
    }
  ];

  return (
    <div className="border-b border-border mb-6">
      <nav className="-mb-px flex space-x-8" aria-label="Tabs">
        {tabs.map((tab) => {
          const isActive = tab.exact 
            ? pathname === tab.href 
            : pathname.startsWith(tab.href);
            
          const Icon = tab.icon;

          return (
            <Link
              key={tab.name}
              href={tab.href}
              className={`
                group inline-flex items-center border-b-2 py-4 px-1 text-sm font-medium
                ${isActive
                  ? 'border-primary text-primary'
                  : 'border-transparent text-muted-foreground hover:border-muted-foreground/30 hover:text-foreground'
                }
              `}
            >
              <Icon
                className={`
                  -ml-0.5 mr-2 h-5 w-5
                  ${isActive ? 'text-primary' : 'text-muted-foreground group-hover:text-foreground'}
                `}
                aria-hidden="true"
              />
              <span>{tab.name}</span>
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
