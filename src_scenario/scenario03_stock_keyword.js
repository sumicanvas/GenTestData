import { equalsFilter, keywordPipeline, runScenario } from "./common.js";

await runScenario({
  scenario: "news_mig 시나리오 3",
  description: "종목코드와 검색어 조건으로 title을 검색합니다.",
  inputs: [
    { key: "shcode", label: "종목코드", example: "005930" },
    { key: "query", label: "검색어", example: "삼성전자" },
  ],
  buildPipeline: ({ indexName, limit, shcode, query, shcodePath }) =>
    keywordPipeline({
      indexName,
      limit,
      query,
      filters: [equalsFilter(shcodePath, shcode)],
    }),
});
