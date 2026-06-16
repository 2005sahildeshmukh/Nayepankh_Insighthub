import { redirect } from "next/navigation";

type PageProps = {
  params: Promise<{
    workspaceId: string;
    datasetId: string;
  }>;
};

export default async function DatasetAnalyticsRedirect({
  params,
}: PageProps) {
  const { workspaceId, datasetId } = await params;

  redirect(
    `/w/${encodeURIComponent(workspaceId)}/analytics?dataset=${encodeURIComponent(datasetId)}`
  );
}
