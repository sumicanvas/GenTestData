import { equalsFilter, keywordPipeline, runScenario } from "./common.js";

await runScenario({
  scenario: "news_mig_500 시나리오 4",
  description: "종목코드, 뉴스구분, 검색어 조건으로 뉴스를 검색합니다.",
  inputs: [
    { key: "shcode", label: "종목코드", example: "005930" },
    { key: "dgubun", label: "뉴스구분", example: "4" },
    { key: "query", label: "검색어", example: "삼성전자 실적" },
  ],
  buildPipeline: ({ indexName, limit, shcode, dgubun, query, shcodePath }) =>
    keywordPipeline({
      indexName,
      limit,
      query,
      filters: [equalsFilter(shcodePath, shcode), equalsFilter("dgubun", dgubun)],
    }),
});
