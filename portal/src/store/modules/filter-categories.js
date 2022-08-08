import { PUBLISHER_DATE_FIELD } from "@/constants";
import { forEach, groupBy, isEmpty, isNil, isNull, union, pull } from "lodash";

import axios from "~/axios";
import { parseSearchMaterialsQuery } from "~/components/_helpers";
import router from "~/router";

function getFiltersForSearch(items) {
  if (isNil(items)) {
    return [];
  }
  return items.reduce((results, item) => {
    // Recursively find selected filters for the children
    if (item.children.length) {
      results = results.concat(getFiltersForSearch(item.children));
    }
    // Add this filter if it is selected
    if (item.selected && !isNull(item.parent)) {
      results.push(item);
    }
    // Also add this filter if a date has been selected
    if (item.external_id === PUBLISHER_DATE_FIELD && (item.dates.start_date || item.dates.end_date)) {
      results.push(item);
    }
    return results;
  }, []);
}

function getFiltersFromQuery(query) {
  let querySearch = parseSearchMaterialsQuery(query);
  let selected = {};
  if (!isEmpty(querySearch.search)) {
    forEach(querySearch.search.filters, (items) => {
      // filters is an object, not an array
      items.reduce((obj, item) => {
        obj[item] = true;
        return obj;
      }, selected);
    });
  }
  return { selected, dateRange: querySearch.dateRange };
}

function loadCategoryFilters(items, selected, dates, opened, showAlls, parent) {
  selected = selected || {};
  dates = isEmpty(dates) ? { start_date: null, end_date: null } : dates;
  opened = opened || [];
  showAlls = showAlls || [];
  let searchId = isNil(parent) ? null : parent.searchId;

  items.forEach((item) => {
    // Set values that might be relevant when loading children
    item.searchId = searchId || item.external_id;
    item.selected = selected[item.external_id] || false;
    // Set relevant properties for date filters
    if (item.external_id === PUBLISHER_DATE_FIELD) {
      item.dates = dates;
      item.selected = dates.start_date || dates.end_date;
    }
    // Load children and retrospecively set some parent properties
    let hasSelectedChildren = loadCategoryFilters(item.children, selected, dates, opened, showAlls, item);
    item.selected = item.selected || hasSelectedChildren;
    item.isOpen = opened.indexOf(item.id) >= 0 || item.selected || hasSelectedChildren;
    item.showAll = showAlls.indexOf(item.id) >= 0;
  });
  return items.some((item) => {
    return item.selected;
  });
}

export default {
  state: {
    filter_categories: null,
    filter_categories_loading: null,
    selection: {},
    byCategoryId: {},
  },
  getters: {
    filter_categories(state) {
      return state.filter_categories;
    },
    filter_categories_loading(state) {
      return state.filter_categories_loading;
    },
    getCategoryById(state) {
      return (itemId, rootId) => {
        const key = isNil(rootId) ? itemId : `${rootId}-${itemId}`;
        return state.byCategoryId[key];
      };
    },
    search_filters(state) {
      if (isNil(state.filter_categories)) {
        return [];
      }
      let selected = getFiltersForSearch(state.filter_categories.results);
      let selectedGroups = groupBy(selected, "searchId");

      const filterMap = {};
      for (const group in selectedGroups) {
        const items = selectedGroups[group].map((item) => {
          return item.external_id;
        });
        filterMap[group] = items;
      }
      return filterMap;
    },
    getFiltersFromQuery() {
      return getFiltersFromQuery;
    },
  },
  actions: {
    async getFilterCategories({ state, commit }) {
      const filters = getFiltersFromQuery(router.currentRoute.query);
      if (window.CATEGORY_FILTERS) {
        loadCategoryFilters(window.CATEGORY_FILTERS, filters.selected, filters.dateRange);
        commit("SET_FILTER_CATEGORIES", window.CATEGORY_FILTERS);
        commit("SET_FILTER_CATEGORIES_LOADING", null);
      } else if (isNil(state.filter_categories_loading) && isEmpty(state.filter_categories)) {
        const promise = axios.get("filter-categories/").then(({ data }) => {
          // Preprocess the filters
          loadCategoryFilters(data, filters.selected, filters.dateRange);
          commit("SET_FILTER_CATEGORIES", data);
          commit("SET_FILTER_CATEGORIES_LOADING", null);
          return data;
        });
        commit("SET_FILTER_CATEGORIES_LOADING", promise);
      }
      return isNil(state.filter_categories_loading) ? state.filter_categories : state.filter_categories_loading;
    },
  },
  mutations: {
    SET_FILTER_CATEGORIES(state, payload) {
      if (isNil(payload)) {
        return;
      }

      state.filter_categories = payload;

      state.byCategoryId = {};
      function setCategoryIds(items) {
        items.forEach((item) => {
          const key = isNull(item.field) ? item.external_id : `${item.field}-${item.external_id}`;
          state.byCategoryId[key] = item;
          setCategoryIds(item.children);
        });
      }
      setCategoryIds(payload);
    },
    SET_FILTER_CATEGORIES_LOADING(state, payload) {
      state.filter_categories_loading = payload;
    },
    SELECT_FILTER_CATEGORIES(state, { category, selection }) {
      state.selection[category] = union(state.selection[category], selection);
    },
    DESELECT_FILTER_CATEGORIES(state, { category, selection }) {
      state.selection[category] = pull(state.selection[category], ...selection);
      if (isEmpty(state.selection[category])) {
        delete state.selection[category];
      }
      if (isEmpty(state.selection)) {
        state.selection = {};
      }
    },
    RESET_FILTER_CATEGORIES_SELECTION(state, selection) {
      state.selection = isEmpty(selection) ? {} : selection;
    },
  },
};
