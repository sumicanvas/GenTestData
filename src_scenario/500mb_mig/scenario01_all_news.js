import { runScenario } from "./common.js";

const DEFAULT_QUERY = "에헤라";

await runScenario({
  scenario: "news_mig_500 시나리오 1",
  description: "title/contents에서 검색어를 검색하고 newscode_ts 최신순으로 조회합니다.",
  buildPipeline: ({ indexName, limit, args }) => {
    const query = args.query || DEFAULT_QUERY;

    return [
      {
        $search: {
          index: indexName,
          text: {
            query,
            path: ["title", "contents"],
          },
          sort: {
            newscode_ts: -1,
          },
        },
      },
      { $limit: limit },
      {
        $project: {
          _id: 1,
          newscode_ts: 1,
          title: 1,
          dgubun: 1,
          shcode: 1,
        },
      },
    ];
  },
});
