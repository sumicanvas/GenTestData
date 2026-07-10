import { equalsFilter, noKeywordPipeline, runScenario } from "./common.js";

await runScenario({
  scenario: "news_mig 시나리오 6",
  description: "종목코드와 뉴스구분 조건으로 해당 뉴스를 최신순으로 조회합니다.",
  inputs: [
    { key: "shcode", label: "종목코드", example: "005930" },
    { key: "dgubun", label: "뉴스구분", example: "P" },
  ],
  buildPipeline: ({ indexName, limit, shcode, dgubun, shcodePath }) =>
    noKeywordPipeline({
      indexName,
      limit,
      filters: [equalsFilter(shcodePath, shcode), equalsFilter("dgubun", dgubun)],
    }),
});
