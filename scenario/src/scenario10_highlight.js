import { keywordPipeline, runScenario } from "./common.js";

await runScenario({
  scenario: "news_mig 시나리오 10",
  description: "Highlight 검색입니다. title 또는 contents의 매칭 영역을 반환합니다.",
  inputs: [{ key: "query", label: "검색어", example: "삼성전자 실적" }],
  buildPipeline: ({ indexName, limit, query }) =>
    keywordPipeline({
      indexName,
      limit,
      query,
      highlight: true,
      searchPath: ["title", "contents"],
      highlightPath: ["title", "contents"],
    }),
});
