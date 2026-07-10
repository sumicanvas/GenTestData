import { keywordPipeline, runScenario } from "./common.js";

await runScenario({
  scenario: "news_mig 시나리오 7",
  description: "검색어만 사용해 전체 뉴스 title을 검색합니다.",
  inputs: [{ key: "query", label: "검색어", example: "삼성전자" }],
  buildPipeline: ({ indexName, limit, query }) => keywordPipeline({ indexName, limit, query }),
});
